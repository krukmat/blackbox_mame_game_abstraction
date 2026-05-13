import entities from "./entities.generated.sample.json" with { type: "json" };
import mechanics from "./mechanics.generated.sample.json" with { type: "json" };

export function loadGeneratedSpecs(): { mechanics: typeof mechanics; entities: typeof entities } {
  return { mechanics, entities };
}
