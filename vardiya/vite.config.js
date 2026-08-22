import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/* base: "./" — uygulama hem alan adının kökünde hem de /vardiya/ gibi bir
   alt klasörde çalışsın diye tüm yollar göreli üretilir.                 */
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { outDir: "dist", assetsDir: "assets" },
});
