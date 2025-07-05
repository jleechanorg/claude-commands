"""
Parallel Dual-Pass Implementation - New endpoints for TASK-019

This module adds the new endpoints needed for parallel dual-pass processing.
To be integrated into main.py
"""

from flask import jsonify, request
from entity_validator import entity_validator
from dual_pass_generator import dual_pass_generator
import logging

def add_parallel_dual_pass_routes(app, get_campaign_info):
    """Add routes for parallel dual-pass optimization"""
    
    @app.route('/api/campaigns/<campaign_id>/enhance-entities', methods=['POST'])
    def enhance_entities(campaign_id):
        """Background endpoint for entity enhancement (Pass 2)"""
        try:
            # Get user ID from session
            user_id = request.cookies.get('user_id')
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Get request data
            data = request.get_json()
            original_response = data.get('original_response', '')
            missing_entities = data.get('missing_entities', [])
            sequence_id = data.get('sequence_id')
            
            # Get campaign info
            campaign_info = get_campaign_info(user_id, campaign_id)
            if not campaign_info:
                return jsonify({'error': 'Campaign not found'}), 404
            
            current_game_state = campaign_info['game_state']
            location = current_game_state.world_data.get('current_location_name', 'Unknown')
            
            # Run Pass 2 - Entity injection using the internal method
            logging.info(f"PARALLEL_DUAL_PASS: Starting background entity enhancement for {len(missing_entities)} entities")
            
            # Create injection prompt
            injection_prompt = dual_pass_generator._create_injection_prompt(
                original_narrative=original_response,
                missing_entities=missing_entities,
                location=location
            )
            
            # Generate enhanced narrative
            from gemini_service import generate_content
            enhanced_narrative = generate_content(injection_prompt)
            
            # Use the injector to refine if needed
            from dual_pass_generator import EntityInjector
            entity_injector = EntityInjector()
            final_narrative = entity_injector.inject_entities_adaptively(
                narrative=enhanced_narrative,
                missing_entities=missing_entities,
                location=location
            )
            
            if final_narrative:
                logging.info(f"PARALLEL_DUAL_PASS: Successfully enhanced narrative with {len(missing_entities)} entities")
                return jsonify({
                    'enhanced_response': final_narrative,
                    'entities_injected': len(missing_entities),
                    'sequence_id': sequence_id,
                    'success': True
                })
            else:
                logging.warning("PARALLEL_DUAL_PASS: Entity enhancement failed")
                return jsonify({
                    'success': False,
                    'error': 'Enhancement failed'
                })
                
        except Exception as e:
            logging.error(f"PARALLEL_DUAL_PASS: Error in enhance_entities: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/campaigns/<campaign_id>/check-enhancement', methods=['GET'])
    def check_enhancement_status(campaign_id):
        """Check if a response needs entity enhancement"""
        try:
            # This endpoint can be used to check if enhancement is complete
            # For now, just return success
            return jsonify({'status': 'ready'})
            
        except Exception as e:
            logging.error(f"PARALLEL_DUAL_PASS: Error checking status: {str(e)}")
            return jsonify({'error': str(e)}), 500