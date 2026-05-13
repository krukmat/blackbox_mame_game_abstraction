import test from "node:test";
import assert from "node:assert/strict";

import { CollisionSystem } from "../src/engine/CollisionSystem.js";
import { EventBus } from "../src/engine/EventBus.js";
import { GameLoop } from "../src/engine/GameLoop.js";
import { PhysicsSystem } from "../src/engine/PhysicsSystem.js";
import { TimeStep } from "../src/engine/TimeStep.js";
import { createEnemy } from "../src/entities/Enemy.js";
import { createPlayer } from "../src/entities/Player.js";
import { createNeutralInput } from "../src/input/InputState.js";
import { loadGeneratedSpecs } from "../src/specs/loadSpecs.js";

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
