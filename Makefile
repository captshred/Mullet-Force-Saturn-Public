# Recovered source is checked against the complete v3 delta/golden-resource lock.
.PHONY: check test
check:
	python3 tools/validate-ricky-jump-chain.py --disc
test:
	python3 tools/validate-ricky-jump-chain.py --test
.PHONY: all setup bootstrap native check test clean
all:
	bash tools/build.sh
setup:
	bash tools/setup.sh
bootstrap:
	bash tools/bootstrap.sh
native:
	bash tools/build.sh --native
legacy-check:
	@if [ "$$(cat build/wingsuit-mode.txt 2>/dev/null)" = 1 ]; then python3 tools/validate-wingsuit.py --disc; fi
	python3 tools/validate-arcade-fx.py
	python3 tools/validate-full-gameplay-sfx2.py
	python3 tools/validate-sfx2.py
	python3 tools/check-public.py
	python3 tools/validate-image.py
	python3 tools/street_validation.py
	python3 tools/parallax_validation.py
	@if [ "$$(cat build/arcade-fx-mode.txt 2>/dev/null)" = 1 ]; then python3 tools/validate-arcade-fx.py --disc && python3 tools/audit-sprite-memory.py > build/sprite-memory.csv; fi
	python3 tools/check-city-neon.py --disc
	python3 tools/check-gameplay-parallax.py --disc
	python3 tools/check-city-cleanup.py --disc
legacy-test: test-live-parallax test-fast-bat test-punch-combo test-city-neon test-city-cleanup
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PLAYER_DEATH=1 -DMF_PLAYER_HURT=1 -DMF_HQ_JUMP=1 -DMF_HQ_TORCH=1 -DMF_JAB_COHESION=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/player_death_test.c -ffunction-sections -fdata-sections -Wl,--gc-sections -o /tmp/mf-player-death
	/tmp/mf-player-death
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_HQ_JUMP=1 -DMF_HQ_TORCH=1 -DMF_JAB_COHESION=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/player_hurt_test.c -ffunction-sections -fdata-sections -Wl,--gc-sections -DMF_PLAYER_HURT=1 -o /tmp/mf-player-hurt
	/tmp/mf-player-hurt
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_CORPORATE_PUNK=1 -DMF_CORPORATE_REFINED=1 -DMF_CP_HQ_COMBAT=1 -Itests/animation_mock -Isrc tests/corporate_hq_test.c src/corporate_animation.c -o /tmp/mf-cphq
	/tmp/mf-cphq
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_JAB_COHESION=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/combat_sfx_test.c src/game.c -o /tmp/mf-custom-combat
	/tmp/mf-custom-combat
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_HQ_JUMP=1 -DMF_HQ_TORCH=1 -DMF_JAB_COHESION=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/hq_jump_bank_test.c -o /tmp/mf-hq-jump-bank
	/tmp/mf-hq-jump-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_HQ_TORCH=1 -DMF_JAB_COHESION=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/hq_torch_bank_test.c -o /tmp/mf-hq-torch-bank
	/tmp/mf-hq-torch-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_JAB_COHESION=1 -DMF_BAT_MOMENTUM=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/jab_repeat_test.c src/game.c -o /tmp/mf-jab-repeat
	/tmp/mf-jab-repeat
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_JAB_COHESION=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/jab_visual_test.c -o /tmp/mf-jab-visual
	/tmp/mf-jab-visual
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/sequence_bank_test.c -o /tmp/mf-sequence-bank
	/tmp/mf-sequence-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_BAT_MOMENTUM=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/momentum_test.c src/game.c -o /tmp/mf-momentum
	/tmp/mf-momentum
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_BAT_MOMENTUM=1 -DMF_BAT_SLIDE_TICKS=12 -DMF_BAT_SLIDE_NUM=1 -DMF_BAT_SLIDE_DEN=2 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/momentum_test.c src/game.c -o /tmp/mf-momentum-tuned
	/tmp/mf-momentum-tuned
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/combat_bank_test.c -o /tmp/mf-momentum-bank
	/tmp/mf-momentum-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/combat_bank_test.c -o /tmp/mf-combat-bank
	/tmp/mf-combat-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/rbv_bank_test.c -o /tmp/mf-rbv-bank
	/tmp/mf-rbv-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_ORIGINAL_THREE_WALK=1 -DMF_ORIGINAL_WALK_SLOW=1 -Itests/animation_mock -Isrc tests/running_bat_visual_test.c src/game.c -o /tmp/mf-rbv-test
	/tmp/mf-rbv-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/running_bank_test.c -o /tmp/mf-running-bank
	/tmp/mf-running-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_DASH_ENABLED=1 -DMF_RUN_BAT=1 -Isrc tests/running_bat_test.c src/game.c -o /tmp/mf-running-bat
	/tmp/mf-running-bat
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_ORIGINAL_THREE_WALK=1 -DMF_ORIGINAL_WALK_SLOW=1 -Itests/animation_mock -Isrc tests/running_animation_test.c src/game.c -o /tmp/mf-running-animation
	/tmp/mf-running-animation
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_DASH_ENABLED=1 -Isrc tests/dash_test.c src/game.c -o /tmp/mf-dash-b-test
	/tmp/mf-dash-b-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_DASH_ENABLED=1 -DMF_DASH_PRESET=15 -Isrc tests/dash_test.c src/game.c -o /tmp/mf-dash-a-test
	/tmp/mf-dash-a-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_DASH_ENABLED=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_ORIGINAL_THREE_WALK=1 -DMF_ORIGINAL_WALK_SLOW=1 -Itests/animation_mock -Isrc tests/dash_animation_test.c src/game.c -o /tmp/mf-dash-animation-test
	/tmp/mf-dash-animation-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_CORPORATE_PUNK=1 -Itests/animation_mock -Isrc tests/corporate_animation_test.c src/corporate_animation.c -o /tmp/mf-corporate-test
	/tmp/mf-corporate-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_CORPORATE_PUNK=1 -DMF_CORPORATE_REFINED=1 -Itests/animation_mock -Isrc tests/corporate_animation_test.c src/corporate_animation.c -o /tmp/mf-corporate-refined-test
	/tmp/mf-corporate-refined-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PLAYABLE_ANIMATION=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/player_animation_test.c src/game.c -o /tmp/mf-original-three-test
	/tmp/mf-original-three-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PLAYABLE_ANIMATION=1 -DMF_ORIGINAL_THREE_WALK=1 -DMF_ORIGINAL_WALK_SLOW=1 -Itests/animation_mock -Isrc tests/player_animation_test.c src/game.c -o /tmp/mf-original-three-slow-test
	/tmp/mf-original-three-slow-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/swagger_bank_test.c -o /tmp/mf-original-three-bank-test
	/tmp/mf-original-three-bank-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PLAYABLE_ANIMATION=1 -DMF_SWAGGER_WALK=1 -Itests/animation_mock -Isrc tests/player_animation_test.c src/game.c -o /tmp/mullet-force-swagger-player-test
	/tmp/mullet-force-swagger-player-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_SWAGGER_WALK=1 -Itests/animation_mock -Isrc tests/swagger_bank_test.c -o /tmp/mullet-force-swagger-bank-test
	/tmp/mullet-force-swagger-bank-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PLAYABLE_ANIMATION=1 -Itests/animation_mock -Isrc tests/player_animation_test.c src/game.c -o /tmp/mullet-force-player-animation-test
	/tmp/mullet-force-player-animation-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/animation_contract_test.c src/game.c -o /tmp/mullet-force-animation-contract-test
	/tmp/mullet-force-animation-contract-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Itests/animation_mock -Isrc tests/animation_preview_test.c -o /tmp/mullet-force-animation-test
	/tmp/mullet-force-animation-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Itests/parallax_mock -Isrc tests/parallax_test.c -o /tmp/mullet-force-parallax-test
	/tmp/mullet-force-parallax-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Itests/street_mock -Isrc tests/street_test.c -o /tmp/mullet-force-street-test
	/tmp/mullet-force-street-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_STREET_LEGACY_CHECK=1 -Itests/street_mock -Isrc tests/street_test.c -o /tmp/mullet-force-street-repro-test
	/tmp/mullet-force-street-repro-test
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_VDP2_STREET=0 -Itests/street_mock -Isrc tests/street_test.c -o /tmp/mullet-force-street-fallback-test
	/tmp/mullet-force-street-fallback-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Itests/gallery_mock -Isrc tests/gallery_test.c -o /tmp/mullet-force-gallery-test
	/tmp/mullet-force-gallery-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/game_test.c src/game.c -o /tmp/mullet-force-game-test
	/tmp/mullet-force-game-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/combat_test.c src/game.c -o /tmp/mullet-force-combat-test
	/tmp/mullet-force-combat-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/coop_test.c src/game.c -o /tmp/mullet-force-coop-test
	/tmp/mullet-force-coop-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/bat_test.c src/game.c -o /tmp/mullet-force-bat-test
	/tmp/mullet-force-bat-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/air_bat_test.c src/game.c -o /tmp/mullet-force-air-bat-test
	/tmp/mullet-force-air-bat-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/torch_test.c src/game.c -o /tmp/mullet-force-torch-test
	/tmp/mullet-force-torch-test
	$(CC) -std=c99 -Wall -Wextra -Werror -Itests/sound_mock -Isrc tests/music_transport_test.c -o /tmp/mullet-force-music-test
	/tmp/mullet-force-music-test
clean:
	rm -rf build
	@if [ -d .deps/joengine/jo_engine ]; then find .deps/joengine/jo_engine -name '*.o' -delete; fi

.PHONY: custom-native
custom-native:
	bash tools/build-custom-combat.sh --native

.PHONY: test-fast-bat
test-fast-bat:
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_FAST_RUNNING_BAT=1 -DMF_BAT_MOMENTUM=1 -DMF_JAB_COHESION=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/fast_bat_test.c src/game.c -o /tmp/mf-fast-bat
	/tmp/mf-fast-bat
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_FAST_RUNNING_BAT=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/fast_bat_bank_test.c -o /tmp/mf-fast-bat-bank
	/tmp/mf-fast-bat-bank
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_FAST_RUNNING_BAT=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/unified_bat_test.c src/game.c -o /tmp/mf-unified-bat
	/tmp/mf-unified-bat
	@for name in combat coop torch; do \
	  $(CC) -std=c99 -Wall -Wextra -Werror -DMF_FAST_RUNNING_BAT=1 -DMF_BAT_MOMENTUM=1 -DMF_JAB_COHESION=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/$${name}_test.c src/game.c -o /tmp/mf-fast-$$name && /tmp/mf-fast-$$name || exit 1; \
	done

.PHONY: test-punch-combo
test-punch-combo:
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PUNCH_COMBO=1 -DMF_FAST_RUNNING_BAT=1 -DMF_BAT_MOMENTUM=1 -DMF_JAB_COHESION=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/punch_combo_test.c src/game.c -o /tmp/mf-combo
	/tmp/mf-combo

	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PUNCH_COMBO=1 -DMF_JAB_COHESION=1 -DMF_FAST_RUNNING_BAT=1 -DMF_ATTACK_SEQUENCE=1 -DMF_BAT_MOMENTUM=1 -DMF_COMBAT_ANIMATION=1 -DMF_PLAYABLE_ANIMATION=1 -DMF_RUNNING_BAT_VISUALS=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -DMF_ORIGINAL_THREE_WALK=1 -Itests/animation_mock -Isrc tests/punch_combo_bank_test.c -o /tmp/mf-combo-bank
	/tmp/mf-combo-bank

	@for name in fast_bat combat coop torch; do 	  $(CC) -std=c99 -Wall -Wextra -Werror -DMF_PUNCH_COMBO=1 -DMF_FAST_RUNNING_BAT=1 -DMF_BAT_MOMENTUM=1 -DMF_JAB_COHESION=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/$${name}_test.c src/game.c -o /tmp/mf-combo-$$name && /tmp/mf-combo-$$name || exit 1; 	done

.PHONY: test-city-neon
test-city-neon:
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_CITY_NEON=1 -Itests/street_mock -Isrc tests/street_test.c -o /tmp/mf-city-neon
	/tmp/mf-city-neon
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_CITY_NEON=1 -DMF_VDP2_STREET=1 -Itests/parallax_mock -Isrc tests/parallax_test.c -o /tmp/mf-city-parallax
	/tmp/mf-city-parallax
	python3 tools/check-city-neon.py
	python3 tests/city_gameplay_test.py

.PHONY: test-city-cleanup
test-city-cleanup:
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_CITY_NEON=1 -DMF_CITY_CLEANUP=1 -Itests/street_mock -Isrc tests/street_test.c -o /tmp/mf-city-cleanup
	/tmp/mf-city-cleanup
	python3 tools/check-city-cleanup.py

.PHONY: test-live-parallax
test-live-parallax:
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_LIVE_CITY_PARALLAX=1 -DMF_CITY_NEON=1 -DMF_CITY_CLEANUP=1 -DMF_VDP2_STREET=1 -Itests/parallax_mock -Isrc tests/live_parallax_test.c -o /tmp/mf-live-parallax
	/tmp/mf-live-parallax
	python3 tools/check-gameplay-parallax.py
.PHONY: test-sfx2
legacy-test: test-sfx2
test-sfx2:
	$(CC) -std=c99 -Wall -Wextra -Werror -Isrc tests/sfx2_test.c -o /tmp/mf-sfx2
	/tmp/mf-sfx2
	$(CC) -std=c99 -Wall -Wextra -Werror -DMF_PUNCH_COMBO=1 -DMF_FAST_RUNNING_BAT=1 -DMF_JAB_COHESION=1 -DMF_RUN_BAT=1 -DMF_DASH_ENABLED=1 -Isrc tests/sfx2_test.c -o /tmp/mf-sfx2-full
	/tmp/mf-sfx2-full

.PHONY: test-full-gameplay-sfx2
legacy-test: test-full-gameplay-sfx2
test-full-gameplay-sfx2:
	python3 tools/test-full-gameplay-sfx2.py

.PHONY: test-arcade-fx
legacy-test: test-arcade-fx
test-arcade-fx:
	python3 tools/test-arcade-fx.py

.PHONY: test-stage-clear
legacy-test: test-stage-clear
test-stage-clear:
	python3 tools/test-stage-clear.py

.PHONY: test-wingsuit
legacy-test: test-wingsuit
test-wingsuit:
	python3 tools/test-wingsuit.py
