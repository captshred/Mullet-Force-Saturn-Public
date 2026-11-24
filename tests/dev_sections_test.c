#include <assert.h>
#include <string.h>
#include "bruce.h"
#include "dev_sections.h"

static void test_section(mf_game *game, mf_section section, int coop)
{
    game->players[1].active = coop;
    game->players[0].health = 1;
    game->players[0].torch = 1;
    game->spark = game->hitstop = 12;
    game->vehicle_dir = -1;
    game->bruce.active = 1;
    game->bruce.state = MF_BRUCE_DEFEATED;
    game->enemies[0].state = MF_ENEMY_IDLE;

    mf_section_init(game, section);

    assert(game->started && !game->paused && game->stage == MF_STAGE_LEVEL1);
    assert(game->camera >= game->camera_floor && game->camera <= MF_WORLD_CAMERA_MAX);
    assert(game->camera_floor == mf_world_checkpoint(game->camera));
    assert(mf_section_current(game, MF_SECTION_OPENING) == section);
    assert(strlen(mf_section_name(section)) > 0);
    assert(!game->spark && !game->hitstop && !game->events && !game->vehicle_dir);
    assert(mf_enemy_count(game) == 0);
    assert(game->players[1].active == coop);
    for (int p = 0; p <= coop; ++p) {
        const mf_player *player = &game->players[p];
        assert(player->health == 100 && !player->height && !player->torch);
        assert(player->y / 256 >= 168 && player->y / 256 <= 229);
        assert(player->x / 256 > game->camera && player->x / 256 < game->camera + 320);
    }

    if (section == MF_SECTION_VEHICLE) {
        mf_game_step(game, 0, 0);
        assert(game->vehicle_tick == 1 && (game->events & MF_VEHICLE_WARNING));
    } else if (section == MF_SECTION_BRUCE) {
        assert(!game->bruce.active && mf_bruce_approach(&game->bruce, game));
        game->bruce.ready = 1;
        mf_game_step(game, 0, 0);
        assert(game->bruce.active && game->bruce.state == MF_BRUCE_ENTRANCE);
        assert(game->bruce.health == MF_BRUCE_MAX_HP && (game->events & MF_BRUCE_ENTRANCE_JUMP));
        game->players[0].x = (MF_BRUCE_LOT_FIRST - 10) * 256;
        assert(mf_section_current(game, section) == section);
        game->bruce.state = MF_BRUCE_READY;
        mf_bruce_receive(&game->bruce, MF_BRUCE_MAX_HP, 0, 1);
        for (int tick = 0; tick < 120; ++tick) mf_game_step(game, 0, 0);
        assert(!game->bruce.health && game->bruce.state == MF_BRUCE_DEFEATED);
        assert(mf_section_current(game, section) == section);
        game->players[0].x = MF_BRUCE_ARCADE_DOORS * 256;
        assert(mf_section_current(game, section) == MF_SECTION_APRON);
    } else if (section == MF_SECTION_APRON) {
        assert(game->bruce.active && game->bruce.state == MF_BRUCE_DEFEATED);
        game->bruce.ready = 1;
        mf_game_step(game, 0, 0);
        assert(!(game->events & (MF_BRUCE_ENTRANCE_JUMP | MF_VEHICLE_WARNING)));
    }
}

static void test_god_and_refill(void)
{
    mf_game game, expected;
    mf_game_init(&game);
    assert(!game.god_mode);
    game.god_mode = 1;
    mf_section_init(&game, MF_SECTION_VEHICLE);
    mf_game_step_coop(&game, (unsigned[2]){0, MF_START}, (unsigned[2]){0, MF_START});
    assert(game.god_mode && game.players[1].active);
    game.players[0].y = game.players[1].y = 214 * 256;
    game.players[1].invulnerable = 0;
    for (int tick = 0; tick < 185; ++tick) mf_game_step(&game, 0, 0);
    assert(game.vehicle_hits == 3u);
    assert(game.players[0].health == 100 && game.players[1].health == 100);

    game.god_mode = 0;
    mf_section_init(&game, MF_SECTION_VEHICLE);
    game.players[0].y = game.players[1].y = 214 * 256;
    for (int tick = 0; tick < 185; ++tick) mf_game_step(&game, 0, 0);
    assert(game.players[0].health == 50 && game.players[1].health == 50);

    game.paused = 1;
    expected = game;
    expected.players[0].health = expected.players[1].health = 100;
    mf_dev_refill_health(&game);
    assert(memcmp(&game, &expected, sizeof game) == 0);
    game.players[1].health = 0;
    game.players[1].defeated = 10;
    mf_dev_refill_health(&game);
    assert(!game.players[1].health && game.players[1].defeated == 10);

    game.god_mode = 1;
    mf_section_init(&game, MF_SECTION_BRUCE);
    assert(game.god_mode);
    mf_game_init(&game);
    assert(!game.god_mode);
}

int main(void)
{
    mf_game game;
    mf_game_init(&game);
    for (int coop = 0; coop < 2; ++coop) {
        for (int cycle = 0; cycle < 5; ++cycle) {
            for (int i = 0; i < MF_SECTION_COUNT; ++i)
                test_section(&game, (mf_section)i, coop);
            for (int i = MF_SECTION_COUNT - 1; i >= 0; --i)
                test_section(&game, (mf_section)i, coop);
            test_section(&game, MF_SECTION_BRUCE, coop);
            test_section(&game, MF_SECTION_BRUCE, coop);
            test_section(&game, MF_SECTION_VEHICLE, coop);
            test_section(&game, MF_SECTION_VEHICLE, coop);
        }
    }
    test_god_and_refill();
    return 0;
}
