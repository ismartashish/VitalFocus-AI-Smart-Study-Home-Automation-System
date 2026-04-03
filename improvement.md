ai-motion-game-engine

core/
    engine_manager.py
    event_bus.py
    config_loader.py
    logger.py

camera/
    camera_manager.py
    camera_stream.py
    frame_buffer.py

vision/
    pose_estimation/
        mediapipe_pose.py
        movenet_pose.py
        openpose_adapter.py

    skeleton/
        skeleton_model.py
        joint_tracker.py
        skeleton_graph.py

    preprocessing/
        frame_normalizer.py
        background_filter.py

gesture/
    gesture_engine.py
    gesture_classifier.py
    gesture_dataset_loader.py

    gestures/
        punch_detector.py
        kick_detector.py
        jump_detector.py
        squat_detector.py
        dodge_detector.py

motion_prediction/
    motion_encoder.py
    motion_transformer.py
    intent_predictor.py

game_input/
    command_mapper.py
    input_dispatcher.py
    control_scheme.py

network/
    socket_server.py
    socket_client.py
    message_protocol.py

game_engine/
    unity_bridge/
        unity_socket_bridge.py

    unreal_bridge/
        unreal_socket_bridge.py

    player_controller/
        player_state.py
        motion_controller.py

    enemy_ai/
        enemy_brain.py
        enemy_behavior_tree.py

physics/
    physics_manager.py
    collision_detector.py

animation/
    skeleton_mapper.py
    animation_blender.py

ui/
    hud_renderer.py
    gesture_debug_overlay.py

training/
    dataset_builder.py
    gesture_trainer.py
    model_exporter.py

tests/
    test_pose_engine.py
    test_gesture_detection.py

assets/
    models/
    animations/
    textures/

scripts/
    launch_engine.py
    calibrate_camera.py

main.py