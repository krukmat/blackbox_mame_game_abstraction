export interface CameraFrame {
  x: number;
  y: number;
  zoom: number;
}

export function createCameraFrame(): CameraFrame {
  return { x: 0, y: 0, zoom: 1 };
}
