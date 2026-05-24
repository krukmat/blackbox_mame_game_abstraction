import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import yaml from "js-yaml";

export interface MechanicsField {
  type: string;
  required?: boolean;
  minimum?: number;
  unit?: string;
  default?: number | string;
  calibration?: string;
  note?: string;
  enum?: string[];
  items?: {
    type: string;
    enum?: string[];
  };
}

export interface MechanicsSection {
  description: string;
  fields: Record<string, MechanicsField>;
  invariants: string[];
  example: Record<string, unknown>;
}

export interface AbstractMechanics {
  schema_version: string;
  game_profile: string;
  calibration_status: string;
  timing: {
    fps: number;
    ms_per_frame: number;
    movement_tolerance_units: number;
    source: string;
  };
  mechanics: Record<string, MechanicsSection>;
}

const MODULE_DIR = dirname(fileURLToPath(import.meta.url));
export const MECHANICS_SPEC_PATH = resolve(
  MODULE_DIR,
  "../../../../specs/mechanics/gng_abstract_mechanics.yaml"
);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function assertAbstractMechanics(value: unknown): asserts value is AbstractMechanics {
  if (!isRecord(value)) {
    throw new Error("Mechanics YAML must parse to an object.");
  }
  if (!isRecord(value.timing)) {
    throw new Error("Mechanics YAML is missing timing data.");
  }
  if (typeof value.timing.ms_per_frame !== "number") {
    throw new Error("Mechanics YAML timing.ms_per_frame must be numeric.");
  }
}

export function loadAbstractMechanics(): AbstractMechanics {
  const rawYaml = readFileSync(MECHANICS_SPEC_PATH, "utf8");
  const parsed = yaml.load(rawYaml);
  assertAbstractMechanics(parsed);
  return parsed;
}
