# App icon

`icon.svg` is the CapitUp app icon (the in-app mark: teal tile, gold trend arrow). `icon-foreground.svg` is the
arrow alone, inside Android's adaptive-icon safe zone.

Regenerate the PNGs after editing the SVGs: `NODE_PATH=$(npm root -g) node render.js` (needs Playwright), then
resize into the Android `mipmap-*`, iOS `AppIcon.appiconset` and `web/icons` folders.

- `icon-1024.png`: App Store icon and the source for every size.
- `play-store-icon-512.png`: Google Play listing icon.

If you have a designer-made logo mark, replace the SVGs (or the PNGs) and regenerate. The arrow is the
Material "trending up" shape (Apache 2.0), the same one the app draws in its header.
