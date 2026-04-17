# CHANGELOG

<!-- version list -->

## v1.7.1 (2026-04-17)

### Bug Fixes

- Enhance pyproject.toml detection with multiple candidate paths
  ([`50c5713`](https://github.com/Hannes0730/Sticker-Hub/commit/50c5713ded28eff55066dc101654b3dc48418848))

- Update asset handling to include pyproject.toml if it exists
  ([`d991912`](https://github.com/Hannes0730/Sticker-Hub/commit/d991912b51aef28afcd1c0e3fcb73846c9febe1c))

### Continuous Integration

- Update release workflow to configure git author and use release token
  ([`a783b03`](https://github.com/Hannes0730/Sticker-Hub/commit/a783b0342e60654a1ed93bac91ac8cedf0715e2d))


## v1.6.0 (2026-04-17)

### Build System

- Update build system configuration for setuptools
  ([`7d634dd`](https://github.com/Hannes0730/Sticker-Hub/commit/7d634ddd975107bbb4b00e13014825dfcda2adda))

### Code Style

- Update sidebar item styling for disabled state
  ([`e70304d`](https://github.com/Hannes0730/Sticker-Hub/commit/e70304d7fe32244a8116b4ab29a14675d9511038))

### Features

- Add application icon support in build configuration
  ([`a6a6c5f`](https://github.com/Hannes0730/Sticker-Hub/commit/a6a6c5f4c7f5310481eb4d95e6ac3b36a2cc203e))

- Add function to prepare Windows icon from PNG source
  ([`e33bbf3`](https://github.com/Hannes0730/Sticker-Hub/commit/e33bbf325e17b819d13c7fbf98e9c7e63fbaa8ca))

- Add function to retrieve asset paths for bundled and local assets
  ([`3971ca1`](https://github.com/Hannes0730/Sticker-Hub/commit/3971ca11b1c43aaf745ad88ee68bd8e14b66dc2a))

- Add runtime icon loading for application window
  ([`b2f0886`](https://github.com/Hannes0730/Sticker-Hub/commit/b2f08860050bc9220632182e224bcc24544f9d5e))


## v1.5.0 (2026-04-17)

### Bug Fixes

- Hide widgets in sticker grid before clearing layout
  ([`ad3b406`](https://github.com/Hannes0730/Sticker-Hub/commit/ad3b40635dfd8c047509cec83511f378b7dd09ee))

### Code Style

- Update sidebar item styling for disabled state
  ([`358b568`](https://github.com/Hannes0730/Sticker-Hub/commit/358b56801b06071cb6629083cacc63205ea01300))

### Features

- Enhance sidebar navigation with grouped headers and custom categories
  ([`aedbd91`](https://github.com/Hannes0730/Sticker-Hub/commit/aedbd9106581103de2772efe7d0b03f9931e6bdd))


## v1.4.0 (2026-04-17)

### Chores

- Exclude StickerHub.spec from .gitignore
  ([`38ea798`](https://github.com/Hannes0730/Sticker-Hub/commit/38ea798d286b8510865b94b2335ab574e9dfdc2f))

### Features

- Add StickerHub.spec for Windows build configuration
  ([`1552d7c`](https://github.com/Hannes0730/Sticker-Hub/commit/1552d7c5a12d3d157cb3d7face8718635c2cc14a))


## v1.3.0 (2026-04-17)

### Chores

- Add .idea/copilotDiffState.xml to .gitignore
  ([`97926e7`](https://github.com/Hannes0730/Sticker-Hub/commit/97926e71fdee036115089c4741081587c19959f1))

- Update .gitignore to exclude Windows virtual environment directories
  ([`144e9c7`](https://github.com/Hannes0730/Sticker-Hub/commit/144e9c7f0e148e1362ecf238768b27e69bf5096d))

- Update .gitignore to include scripts directory and Python files
  ([`abd9d2b`](https://github.com/Hannes0730/Sticker-Hub/commit/abd9d2bbc4d4f4abdbc99c58a83eed355eb2587f))

### Continuous Integration

- Add check for missing build script in Windows asset release
  ([`1a2e836`](https://github.com/Hannes0730/Sticker-Hub/commit/1a2e836e2f3e2341af138a3b374fd27faa07d3ec))

### Features

- Add build script for Windows with error handling guidance
  ([`c3437a8`](https://github.com/Hannes0730/Sticker-Hub/commit/c3437a873533edfaa826b5d0ae03bf2850d544ca))


## v1.2.0 (2026-04-17)

### Continuous Integration

- Validate release token in release workflow
  ([`2cdb31c`](https://github.com/Hannes0730/Sticker-Hub/commit/2cdb31cb24ce4e7aea346c2487762ce16dc3e9b6))

### Documentation

- Update README with URL upgrade functionality details
  ([`7ceaa32`](https://github.com/Hannes0730/Sticker-Hub/commit/7ceaa320b88168090c59bb848b0019b1ad2fd4d4))

### Features

- Add functionality to upgrade sticker URLs and handle duplicates
  ([`166a85c`](https://github.com/Hannes0730/Sticker-Hub/commit/166a85cf4595be528d18678fa5785923faac09c7))

- Add image upscale functionality to conversion methods
  ([`00e08c6`](https://github.com/Hannes0730/Sticker-Hub/commit/00e08c6a657c02c9ce9e4b73d1e4222a73e032a2))

- Add thumbnail size configuration to download worker
  ([`5f3b4a5`](https://github.com/Hannes0730/Sticker-Hub/commit/5f3b4a5cb529cc0eed616883084d60c44098abd7))

- Add thumbnail size parameter to download worker
  ([`0338f6b`](https://github.com/Hannes0730/Sticker-Hub/commit/0338f6b4c43761026f573deebe8ee5bad94b97b5))

- Add upgrade_sticker_urls_file to module exports
  ([`ef0932f`](https://github.com/Hannes0730/Sticker-Hub/commit/ef0932fb6849d20fe8c5e542d1d9a89e2737debe))

- Add URL upgrade functionality and preview quality selection
  ([`ab99772`](https://github.com/Hannes0730/Sticker-Hub/commit/ab997725a0f5e2380cb3dc5a465c141d238ed125))


## v1.1.0 (2026-04-17)

### Continuous Integration

- Update Windows asset release workflow to include executable
  ([`034a3d1`](https://github.com/Hannes0730/Sticker-Hub/commit/034a3d10d9a5a357632250ae357ae1c5c0236c53))

### Features

- Add version retrieval functionality from pyproject.toml
  ([`ca6b6bb`](https://github.com/Hannes0730/Sticker-Hub/commit/ca6b6bb415aa1dba61100d208b1b6ced57fedcb2))

- Add versioning to the application
  ([`d17f489`](https://github.com/Hannes0730/Sticker-Hub/commit/d17f48902b0b90ce0cd94ed72f2525f8140cfc32))

- Display application version in the main window
  ([`aa5e00d`](https://github.com/Hannes0730/Sticker-Hub/commit/aa5e00dad6f0c14dbbd862861d9274097d438a2a))

- Print application version in smoke test
  ([`f12a3d6`](https://github.com/Hannes0730/Sticker-Hub/commit/f12a3d675e986ea4ece078087c64afea1d78412f))


## v1.0.0 (2026-04-17)

- Initial Release
