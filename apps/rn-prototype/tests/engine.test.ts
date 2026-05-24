import test from "node:test";
import assert from "node:assert/strict";

import { CollisionSystem } from "../src/engine/CollisionSystem.js";
import { EventBus } from "../src/engine/EventBus.js";
import { GameLoop } from "../src/engine/GameLoop.js";
import { CALIBRATED_PHYSICS_CONFIG, PhysicsSystem } from "../src/engine/PhysicsSystem.js";
import { TimeStep } from "../src/engine/TimeStep.js";
import { createEnemy } from "../src/entities/Enemy.js";
import { createPlayer } from "../src/entities/Player.js";
import { createNeutralInput } from "../src/input/InputState.js";
import { loadGeneratedSpecs } from "../src/specs/loadSpecs.js";
import { loadAbstractMechanics } from "../src/specs/mechanicsLoader.js";

test("physics step is deterministic", () => {
  const physics = new PhysicsSystem({ gravity: 9.8, moveSpeed: 3, jumpVelocity: 6 });
  const loop = new GameLoop(new TimeStep(16), physics, new EventBus());
  const input = { ...createNeutralInput(), right: true };

  const first = loop.tick(createPlayer(), input);
  const second = loop.tick(createPlayer(), input);

  assert.deepEqual(first, second);
});

test("collision outcomes detect overlap", () => {
  const player = createPlayer();
  const enemy = createEnemy();
  enemy.position.x = 0.5;

  const result = new CollisionSystem().collide(player, enemy);
  assert.equal(result.collided, true);
  assert.deepEqual(result.pair, ["player", "enemy_patrol"]);
});

test("generated specs load cleanly", () => {
  const specs = loadGeneratedSpecs();
  assert.equal(specs.mechanics.mechanic_id, "sample_side_scroll");
  assert.equal(specs.entities.entities[0].id, "player");
});

test("abstract mechanics loader reads public YAML timing", () => {
  const mechanics = loadAbstractMechanics();

  assert.equal(mechanics.game_profile, "gngb");
  assert.equal(mechanics.timing.ms_per_frame, 16.768);
});

test("TimeStep can be created from loaded mechanics timing", () => {
  const mechanics = loadAbstractMechanics();
  const timeStep = TimeStep.fromMechanics(mechanics);

  assert.equal(timeStep.fixedDeltaMs, 16.768);
  assert.equal(timeStep.seconds(), 0.016768);
});

// T11.3 — assert CALIBRATED_PHYSICS_CONFIG does not use hardcoded stub values.
// These stubs (9.8, 3, 6) were the placeholder defaults before physics calibration.
test("CALIBRATED_PHYSICS_CONFIG does not use hardcoded gravity stub", () => {
  assert.notEqual(
    CALIBRATED_PHYSICS_CONFIG.gravity,
    9.8,
    "gravity must be calibrated from trace, not the 9.8 stub"
  );
});

test("CALIBRATED_PHYSICS_CONFIG does not use hardcoded moveSpeed stub", () => {
  assert.notEqual(
    CALIBRATED_PHYSICS_CONFIG.moveSpeed,
    3,
    "moveSpeed must be calibrated from trace, not the 3 stub"
  );
});

test("CALIBRATED_PHYSICS_CONFIG does not use hardcoded jumpVelocity stub", () => {
  assert.notEqual(
    CALIBRATED_PHYSICS_CONFIG.jumpVelocity,
    6,
    "jumpVelocity must be calibrated from trace, not the 6 stub"
  );
});
