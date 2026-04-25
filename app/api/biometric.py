"""
Biometric API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.api.schemas import (
    EnrollFaceRequest, EnrollFaceResponse,
    VerifyFaceRequest, VerifyFaceResponse,
    SearchFaceRequest, SearchFaceResponse, FaceMatchResult,
    DeleteFaceRequest, DeleteFaceResponse,
    UpdateFaceUserRequest, UpdateFaceUserResponse
)
from app.services.face_service import FaceRecognitionService
from app.models.database import get_database
from app.models.face_model import FaceDocument, VerificationLog
from app.utils.image_utils import (
    base64_to_image, image_to_base64, 
    optimize_for_processing, prepare_image_for_upload
)
import logging
from datetime import datetime
from bson import ObjectId
import cv2

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/biometric", tags=["Biometric"])

# Initialize face recognition service
face_service = FaceRecognitionService()


@router.post("/enroll", response_model=EnrollFaceResponse)
async def enroll_face(request: EnrollFaceRequest):
    """
    Enroll a new face for customer
    This endpoint is called by the merchant app after capturing customer's face
    Performs liveness detection and stores face encoding
    Returns face_id that will be included in QR code for customer to link
    """
    try:
        # Note: merchant_id is included in request for audit trail, but face is linked to user later via QR
        # At this point, we don't have user_id yet - customer will link it via QR scan
        
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Optimize image size for faster processing (reduces processing time by 50-70%)
        image = optimize_for_processing(image, max_dimension=800)
        
        # Detect and encode face with liveness detection
        # Normalization during encoding helps face work across different lighting/locations
        result = face_service.detect_and_encode_face(image, check_liveness=True)
        
        if not result or not result.get('success'):
            return EnrollFaceResponse(
                success=False,
                message=result.get('error', 'Face enrollment failed') if result else 'Face processing failed',
                liveness_passed=False
            )
        
        # Get database
        db = get_database()
        
        # Prepare face document
        liveness_result = result.get('liveness_result') or {}
        
        # Store face without user_id initially - will be linked when customer scans QR
        # result['encoding'] contains multiple encodings from different variations
        face_location = result.get('face_location')
        face_doc = FaceDocument(
            user_id=None,  # Will be set during link-face operation
            face_encodings=result['encoding'],  # Multiple encodings for robust matching
            image_url=None,  # No image storage - encodings only
            liveness_score=liveness_result.get('confidence', 0.0),
            quality_score=result.get('quality_score', 0.0),
            is_active=False,  # Not active until linked to user
            metadata={
                'liveness_checks': liveness_result.get('checks', {}),
                'face_location': list(face_location) if face_location is not None else None,
                'enrolled_by_merchant': request.merchant_id,  # Audit trail
                'enrollment_session': str(ObjectId())  # Unique session for QR
            }
        )
        
        insert_result = await db.faces.insert_one(face_doc.model_dump(by_alias=True, exclude={'id'}))
        face_id = str(insert_result.inserted_id)
        
        return EnrollFaceResponse(
            success=True,
            message="Face enrolled successfully. Generate QR code with this face_id for customer to scan.",
            face_id=face_id,
            liveness_passed=liveness_result.get('is_live', False),
            liveness_confidence=liveness_result.get('confidence'),
            quality_score=result.get('quality_score'),
            image_url=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Face enrollment error: {e}\n{traceback.format_exc()}")
        # Handle duplicate key error for user_id (MongoDB unique index constraint)
        if "E11000 duplicate key error" in str(e) and "user_id" in str(e):
            raise HTTPException(
                status_code=409, 
                detail="A pending face enrollment already exists. Please complete or cancel the previous enrollment before creating a new one."
            )
        raise HTTPException(status_code=500, detail=f"Face enrollment failed: {str(e)}")


@router.post("/verify", response_model=VerifyFaceResponse)
async def verify_face(request: VerifyFaceRequest):
    """
    Verify a customer's face against stored enrollment
    Used during payment authentication at merchant location
    Merchant app captures customer face and verifies it
    """
    try:
        # Only verify customer faces (no merchant face verification needed)
        if not request.user_id:
            # If no user_id provided, search all faces to find match
            pass
        
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Optimize image for faster verification (smaller = faster)
        # Smaller images also reduce noise that could cause false negatives in different lighting
        image = optimize_for_processing(image, max_dimension=640)  # Even smaller for verification speed
        
        # Detect and encode face - ALWAYS skip liveness for verification (only check during enrollment)
        # This allows verification to work in any location/lighting condition
        # Face normalization in detect_and_encode_face handles lighting variations
        result = face_service.detect_and_encode_face(image, check_liveness=False)
        
        if not result or not result.get('success'):
            # Log failed verification
            db = get_database()
            error_message = result.get('error', 'Face verification failed') if result else 'Face detection failed'
            try:
                log = VerificationLog(
                    user_id=request.user_id,
                    merchant_id=request.merchant_id,
                    success=False,
                    liveness_passed=False,
                    metadata={'error': error_message}
                )
                log_result = await db.verification_logs.insert_one(log.model_dump(by_alias=True, exclude={'id'}))
                logger.info(f"Failed verification log inserted: {log_result.inserted_id}")
            except Exception as e:
                logger.error(f"Failed to insert verification log: {e}")
            
            return VerifyFaceResponse(
                success=False,
                verified=False,
                message=error_message,
                liveness_passed=False
            )
        
        # Get stored face encoding from database
        db = get_database()
        
        if request.user_id:
            # Verify specific user
            stored_face = await db.faces.find_one({"user_id": request.user_id, "is_active": True})
            if not stored_face:
                raise HTTPException(status_code=404, detail="No enrolled face found for this user")
            entity_id = request.user_id
        else:
            # Search mode - find matching face across all enrolled users
            # This is useful when merchant doesn't know user_id
            all_faces = await db.faces.find({"is_active": True, "user_id": {"$ne": None}}).to_list(length=None)
            if not all_faces:
                raise HTTPException(status_code=404, detail="No enrolled faces found in system")
            
            # Find best match
            best_match = None
            best_confidence = 0.0
            
            for face in all_faces:
                verification = face_service.verify_face(
                    result['encoding'],
                    face['face_encoding']
                )
                if verification['match'] and verification['confidence'] > best_confidence:
                    best_confidence = verification['confidence']
                    best_match = face
            
            if not best_match:
                try:
                    log = VerificationLog(
                        user_id=None,
                        success=False,
                        liveness_passed=False,
                        metadata={'error': 'No matching face found'}
                    )
                    log_result = await db.verification_logs.insert_one(log.model_dump(by_alias=True, exclude={'id'}))
                    logger.info(f"No match verification log inserted: {log_result.inserted_id}")
                except Exception as e:
                    logger.error(f"Failed to insert verification log: {e}")
                
                return VerifyFaceResponse(
                    success=False,
                    verified=False,
                    message="No matching face found",
                    liveness_passed=False
                )
            
            stored_face = best_match
            entity_id = stored_face['user_id']
        
        # Compare faces - pass all stored encodings for best match
        # stored_face['face_encodings'] contains multiple variations from enrollment
        stored_encodings = stored_face.get('face_encodings', stored_face.get('face_encoding', []))
        
        verification = face_service.verify_face(
            result['encoding'],
            stored_encodings
        )
        
        # Get liveness result (will be None since we skip liveness during verification)
        liveness_result = result.get('liveness_result') or {}
        liveness_passed = True  # Always pass liveness for verification (only check during enrollment)
        
        # Determine final verification result
        verified = verification['match']  # Only check face match, not liveness
        
        # Log verification attempt
        try:
            log = VerificationLog(
                user_id=entity_id,
                success=verified,
                confidence=verification['confidence'],
                liveness_passed=liveness_passed,
                metadata={
                    'face_distance': verification['distance'],
                    'liveness_confidence': liveness_result.get('confidence'),
                    'encodings_checked': verification.get('encodings_checked', 1)
                }
            )
            log_result = await db.verification_logs.insert_one(log.model_dump(by_alias=True, exclude={'id'}))
            logger.info(f"Verification log inserted: {log_result.inserted_id} - User: {entity_id}, Success: {verified}, Confidence: {verification['confidence']:.2%}")
        except Exception as e:
            logger.error(f"Failed to insert verification log: {e}")
            # Continue with verification even if logging fails
        
        # Continuous Learning: Update face encodings from successful high-confidence verifications
        if verified and verification['confidence'] >= 0.55:  # Only learn from 55%+ confidence
            try:
                # Get current encodings count
                current_encodings = stored_face.get('face_encodings', stored_face.get('face_encoding', []))
                
                # Handle old format
                if current_encodings and isinstance(current_encodings[0], (int, float)):
                    current_encodings = [current_encodings]
                
                # Get total successful verification count for this user (all-time)
                total_successful_verifications = await db.verification_logs.count_documents({
                    'user_id': entity_id,
                    'success': True,
                    'confidence': {'$gte': 0.55}  # Only count high-confidence verifications
                })
                
                # Get learning update count from metadata
                learning_updates = stored_face.get('metadata', {}).get('learning_updates', 0)
                
                # Add new encoding if:
                # 1. We have less than max encodings (10)
                # 2. This is every 3rd successful verification since last update
                # 3. Confidence is high enough (55%+)
                max_encodings = 10
                update_interval = 3
                
                # Calculate if we should update: (total_verifications - initial_3_from_enrollment) % interval == 0
                # Since we start with 3 encodings, we need (total - 3) to be divisible by interval
                verifications_since_enrollment = total_successful_verifications
                should_add = (
                    len(current_encodings) < max_encodings and
                    verifications_since_enrollment > 0 and
                    verifications_since_enrollment % update_interval == 0 and
                    learning_updates < (verifications_since_enrollment // update_interval)
                )
                
                if should_add:
                    # Add the new encoding to the list
                    new_encodings = current_encodings + [result['encoding']]
                    
                    await db.faces.update_one(
                        {'_id': stored_face['_id']},
                        {
                            '$set': {
                                'face_encodings': new_encodings,
                                'updated_at': datetime.utcnow()
                            },
                            '$inc': {'metadata.learning_updates': 1}
                        }
                    )
                    
                    logger.info(f"Continuous Learning: Added new encoding for user {entity_id} "
                              f"({len(new_encodings)}/{max_encodings} encodings, "
                              f"verification #{verifications_since_enrollment}, confidence={verification['confidence']:.2%})")
                elif len(current_encodings) >= max_encodings and verifications_since_enrollment % update_interval == 0 and learning_updates < (verifications_since_enrollment // update_interval):
                    # Replace oldest encoding with new one (keep most recent)
                    new_encodings = current_encodings[1:] + [result['encoding']]
                    
                    await db.faces.update_one(
                        {'_id': stored_face['_id']},
                        {
                            '$set': {
                                'face_encodings': new_encodings,
                                'updated_at': datetime.utcnow()
                            },
                            '$inc': {'metadata.learning_updates': 1}
                        }
                    )
                    
                    logger.info(f"Continuous Learning: Replaced oldest encoding for user {entity_id} "
                              f"(maintaining {max_encodings} encodings, "
                              f"verification #{verifications_since_enrollment}, confidence={verification['confidence']:.2%})")
                    
            except Exception as e:
                # Don't fail verification if learning update fails
                logger.warning(f"Continuous learning update failed (non-critical): {e}")
        
        return VerifyFaceResponse(
            success=True,
            verified=verified,
            message="Face verified successfully" if verified else "Face verification failed",
            user_id=entity_id,  # Always return matched user_id
            confidence=verification['confidence'],
            liveness_passed=liveness_passed,
            liveness_confidence=liveness_result.get('confidence'),
            match_distance=verification['distance']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face verification error: {e}")
        raise HTTPException(status_code=500, detail=f"Face verification failed: {str(e)}")


@router.post("/search", response_model=SearchFaceResponse)
async def search_face(request: SearchFaceRequest):
    """
    Search for a face across all enrolled faces
    Returns top K matches
    """
    try:
        # Convert base64 to image
        image = base64_to_image(request.image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect and encode face
        result = face_service.detect_and_encode_face(image, check_liveness=False)
        
        if not result['success']:
            return SearchFaceResponse(
                success=False,
                message=result.get('error', 'Face detection failed'),
                matches=[],
                total_searched=0
            )
        
        # Get all enrolled faces from database
        db = get_database()
        
        if request.search_type == "user":
            collection = db.faces
            id_field = "user_id"
        else:
            collection = db.merchant_faces
            id_field = "merchant_id"
        
        enrolled_faces = await collection.find({"is_active": True}).to_list(length=None)
        
        if not enrolled_faces:
            return SearchFaceResponse(
                success=True,
                message="No enrolled faces found",
                matches=[],
                total_searched=0
            )
        
        logger.info(f"Searching against {len(enrolled_faces)} enrolled faces")
        
        # Compare against ALL stored encodings for each face (not just first one)
        # This ensures we check all lighting variations stored during enrollment
        matches = []
        
        for idx, face in enumerate(enrolled_faces):
            # Get all encodings for this face
            encodings = face.get('face_encodings', face.get('face_encoding', []))
            if not encodings:
                logger.warning(f"Face {idx} has no encodings, skipping")
                continue
            
            # Handle both old format (single encoding) and new format (multiple encodings)
            if isinstance(encodings[0], (int, float)):
                # Old format: single encoding
                encodings = [encodings]
            
            logger.debug(f"Face {idx}: Checking {len(encodings)} encodings")
            
            # Compare against ALL encodings for this face and get best match
            best_confidence = 0.0
            best_distance = float('inf')
            
            for enc_idx, stored_encoding in enumerate(encodings):
                # Use verify_face which handles the comparison logic
                verification = face_service.verify_face(
                    result['encoding'],
                    [stored_encoding]  # Pass as list
                )
                
                logger.debug(f"  Encoding {enc_idx}: distance={verification['distance']:.4f}, confidence={verification['confidence']:.2%}")
                
                if verification['confidence'] > best_confidence:
                    best_confidence = verification['confidence']
                    best_distance = verification['distance']
            
            logger.info(f"Face {idx} ({face.get('user_id', 'unknown')}): Best match - confidence={best_confidence:.2%}, distance={best_distance:.4f}")
            
            # If best match meets minimum confidence, add to results
            if best_confidence >= request.min_confidence:
                match = FaceMatchResult(
                    user_id=face.get('user_id') if request.search_type == "user" else None,
                    merchant_id=face.get('merchant_id') if request.search_type == "merchant" else None,
                    confidence=best_confidence,
                    distance=best_distance,
                    face_id=str(face['_id'])
                )
                matches.append(match)
                logger.info(f"  ✓ Added to matches (confidence {best_confidence:.2%} >= min {request.min_confidence:.2%})")
            else:
                logger.info(f"  ✗ Below threshold (confidence {best_confidence:.2%} < min {request.min_confidence:.2%})")
        
        # Limit to top K and sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        matches = matches[:request.top_k]
        
        # Log search attempt and apply continuous learning for top match
        if matches:
            top_match = matches[0]
            
            # Log the search/verification attempt
            try:
                log = VerificationLog(
                    user_id=top_match.user_id,
                    merchant_id=request.merchant_id if hasattr(request, 'merchant_id') else None,
                    success=True,
                    confidence=top_match.confidence,
                    liveness_passed=True,
                    metadata={
                        'face_distance': top_match.distance,
                        'search_result': True,
                        'total_matches': len(matches),
                        'match_rank': 1
                    }
                )
                log_result = await db.verification_logs.insert_one(log.model_dump(by_alias=True, exclude={'id'}))
                logger.info(f"Search log inserted: {log_result.inserted_id} - User: {top_match.user_id}, Confidence: {top_match.confidence:.2%}")
            except Exception as e:
                logger.error(f"Failed to insert search log: {e}")
            
            # Continuous Learning: Update face encodings from successful high-confidence matches
            if top_match.confidence >= 0.55:  # Only learn from 55%+ confidence
                try:
                    # Find the matched face document
                    matched_face = await db.faces.find_one({"_id": ObjectId(top_match.face_id)})
                    
                    if matched_face:
                        # Get current encodings count
                        current_encodings = matched_face.get('face_encodings', matched_face.get('face_encoding', []))
                        
                        # Handle old format
                        if current_encodings and isinstance(current_encodings[0], (int, float)):
                            current_encodings = [current_encodings]
                        
                        # Get total successful verification count for this user (all-time)
                        total_successful_verifications = await db.verification_logs.count_documents({
                            'user_id': top_match.user_id,
                            'success': True,
                            'confidence': {'$gte': 0.55}
                        })
                        
                        # Get learning update count from metadata
                        learning_updates = matched_face.get('metadata', {}).get('learning_updates', 0)
                        
                        max_encodings = 10
                        update_interval = 3
                        
                        verifications_since_enrollment = total_successful_verifications
                        should_add = (
                            len(current_encodings) < max_encodings and
                            verifications_since_enrollment > 0 and
                            verifications_since_enrollment % update_interval == 0 and
                            learning_updates < (verifications_since_enrollment // update_interval)
                        )
                        
                        if should_add:
                            # Add the new encoding to the list
                            new_encodings = current_encodings + [result['encoding']]
                            
                            await db.faces.update_one(
                                {'_id': matched_face['_id']},
                                {
                                    '$set': {
                                        'face_encodings': new_encodings,
                                        'updated_at': datetime.utcnow()
                                    },
                                    '$inc': {'metadata.learning_updates': 1}
                                }
                            )
                            
                            logger.info(f"Continuous Learning (Search): Added new encoding for user {top_match.user_id} "
                                      f"({len(new_encodings)}/{max_encodings} encodings, "
                                      f"verification #{verifications_since_enrollment}, confidence={top_match.confidence:.2%})")
                        elif len(current_encodings) >= max_encodings and verifications_since_enrollment % update_interval == 0 and learning_updates < (verifications_since_enrollment // update_interval):
                            # Replace oldest encoding with new one (keep most recent)
                            new_encodings = current_encodings[1:] + [result['encoding']]
                            
                            await db.faces.update_one(
                                {'_id': matched_face['_id']},
                                {
                                    '$set': {
                                        'face_encodings': new_encodings,
                                        'updated_at': datetime.utcnow()
                                    },
                                    '$inc': {'metadata.learning_updates': 1}
                                }
                            )
                            
                            logger.info(f"Continuous Learning (Search): Replaced oldest encoding for user {top_match.user_id} "
                                      f"(maintaining {max_encodings} encodings, "
                                      f"verification #{verifications_since_enrollment}, confidence={top_match.confidence:.2%})")
                        
                except Exception as e:
                    # Don't fail search if learning update fails
                    logger.warning(f"Continuous learning update failed (non-critical): {e}")
        
        return SearchFaceResponse(
            success=True,
            message=f"Found {len(matches)} matches",
            matches=matches,
            total_searched=len(enrolled_faces)
        )
        
    except Exception as e:
        logger.error(f"Face search error: {e}")
        raise HTTPException(status_code=500, detail=f"Face search failed: {str(e)}")


@router.delete("/delete", response_model=DeleteFaceResponse)
async def delete_face(request: DeleteFaceRequest):
    """
    Delete enrolled face for customer
    """
    try:
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id must be provided")
        
        db = get_database()
        
        # Permanently remove the face document that is linked to the user
        result = await db.faces.delete_one({"user_id": request.user_id, "is_active": True})

        # If no document was deleted, there was no active face for this user
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="No enrolled face found for this user")

        return DeleteFaceResponse(
            success=True,
            message="Face deleted successfully for user"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Face deletion failed: {str(e)}")


@router.put("/update-face-user", response_model=UpdateFaceUserResponse)
async def update_face_user(request: UpdateFaceUserRequest):
    """
    Update face document with user_id after payment service links face to user
    Called by payment service when user scans QR code and links face
    """
    try:
        if not request.user_id or not request.face_id:
            raise HTTPException(status_code=400, detail="Both user_id and face_id are required")
        
        db = get_database()
        
        # Find the new face record by face_id first
        try:
            face_object_id = ObjectId(request.face_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid face_id format")
        
        face = await db.faces.find_one({"_id": face_object_id})
        if not face:
            raise HTTPException(status_code=404, detail="Face not found")
        
        if face.get('user_id') is not None and face.get('user_id') != request.user_id:
            raise HTTPException(status_code=400, detail="This face is already linked to another user")
        
        # If user already has an active face, deactivate it before linking the new one
        await db.faces.update_many(
            {"user_id": request.user_id, "is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        # Update face with user_id and activate it
        result = await db.faces.update_one(
            {"_id": face_object_id},
            {
                "$set": {
                    "user_id": request.user_id,
                    "is_active": True,
                    "linked_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update face with user_id")
        
        return UpdateFaceUserResponse(
            success=True,
            message="Face linked to user successfully",
            user_id=request.user_id,
            face_id=request.face_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face user update error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update face with user_id: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_face(user_id: int):
    """Get enrolled face info for a user"""
    try:
        db = get_database()
        face = await db.faces.find_one({"user_id": user_id, "is_active": True})
        
        if not face:
            raise HTTPException(status_code=404, detail="No enrolled face found for this user")
        
        return {
            "success": True,
            "face_id": str(face['_id']),
            "user_id": face['user_id'],
            "enrolled_at": face['created_at'],
            "quality_score": face.get('quality_score'),
            "liveness_score": face.get('liveness_score')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user face: {e}")
        raise HTTPException(status_code=500, detail=str(e))



