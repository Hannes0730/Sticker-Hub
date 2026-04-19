# CHANGELOG

<!-- version list -->

## v1.15.0 (2026-04-19)

### Documentation

- Update README for SQLite migration and data locations
  ([`c1b3f76`](https://github.com/Hannes0730/Sticker-Hub/commit/c1b3f765cbbf4c539476966bc2b49ef6bbce521c))

### Features

- Add catalog database status display in main window
  ([`a55e8d7`](https://github.com/Hannes0730/Sticker-Hub/commit/a55e8d7558daac1aa9f080978fa89f67e427c34b))

- Add function to retrieve catalog database path
  ([`6a4c5eb`](https://github.com/Hannes0730/Sticker-Hub/commit/6a4c5eb7766ca6ed835b2e5d44476bd5f6575525))

- Add get_catalog_db_status function to module exports
  ([`b7052e9`](https://github.com/Hannes0730/Sticker-Hub/commit/b7052e97a3226b23a4b5dad53412c8f230bc1ded))

- Migrate catalog loading to SQLite database
  ([`5e5d8ae`](https://github.com/Hannes0730/Sticker-Hub/commit/5e5d8ae4eb7a2ce3ed74201231b03af9472bb172))


## v1.14.1 (2026-04-18)

### Bug Fixes

- Improve installer launch process with error handling and retry logic
  ([`5309764`](https://github.com/Hannes0730/Sticker-Hub/commit/5309764679bf8cd2872711d961fad75e0247e3d0))


## v1.14.0 (2026-04-18)

### Bug Fixes

- Update asset ranking logic for in-app updates to prioritize ZIP files
  ([`c5d73a1`](https://github.com/Hannes0730/Sticker-Hub/commit/c5d73a10861aa74d3545464da123b9c676368f6e))

### Features

- Enhance in-app update process with installation prompts and progress feedback
  ([`88d6c38`](https://github.com/Hannes0730/Sticker-Hub/commit/88d6c38aa169eaa31a45998f207b329bdf81fe63))

- Expose update installation functions in module exports
  ([`a569464`](https://github.com/Hannes0730/Sticker-Hub/commit/a569464bae0884a5157cc46a2b6b5c19594b7ba2))

- Implement in-app update service for Windows
  ([`ea8d078`](https://github.com/Hannes0730/Sticker-Hub/commit/ea8d078c2cdac29e7e0dd793ffaba03808a3328d))


## v1.13.1 (2026-04-18)

### Bug Fixes

- Normalize capitalization for category, name, and pack name fields
  ([`8f94ed9`](https://github.com/Hannes0730/Sticker-Hub/commit/8f94ed9880038b0e1b6a7d36e425722e509d35de))


## v1.13.0 (2026-04-18)

### Chores

- Update dependencies and version for sticker-hub package
  ([`33d5647`](https://github.com/Hannes0730/Sticker-Hub/commit/33d56479ad52023f0056650be7bdd1e2d8ff903e))

### Features

- Add update check functionality with user prompts for new versions
  ([`a1b6c40`](https://github.com/Hannes0730/Sticker-Hub/commit/a1b6c40b7e6abc85e0bd4f3415860ddef384edff))

- Add update service functions to module exports
  ([`01ef56a`](https://github.com/Hannes0730/Sticker-Hub/commit/01ef56a0d30d2eac92bd986009da47f0a9da943a))

- Implement update service to check for latest releases
  ([`cc53df7`](https://github.com/Hannes0730/Sticker-Hub/commit/cc53df76f68229053aefeb974dda46579b4fda10))


## v1.12.0 (2026-04-18)

### Features

- Add URL deduplication to image resolution process
  ([`99f8788`](https://github.com/Hannes0730/Sticker-Hub/commit/99f8788384e03baefcf87bcb186d421d6283392c))

- Add URL deduplication to image resolution process
  ([`9b9bc75`](https://github.com/Hannes0730/Sticker-Hub/commit/9b9bc758460951ee346a33e9741a163ea6edeb7b))

- Enhance URL filtering by adding additional query parameters to exclusion list
  ([`c90e98c`](https://github.com/Hannes0730/Sticker-Hub/commit/c90e98caeed325a4f21766a710ce6291a53d1465))

- Implement API-based sticker pack resolution and enhance URL filtering
  ([`42654a1`](https://github.com/Hannes0730/Sticker-Hub/commit/42654a11650be6042977e3f058b204553eb00001))


## v1.11.1 (2026-04-18)

### Bug Fixes

- Improve layout handling on resize events in main window
  ([`a3da24e`](https://github.com/Hannes0730/Sticker-Hub/commit/a3da24ed9f40dfab5058dc516e226a49301d8e4f))

- Optimize grid layout handling on card visibility changes
  ([`73de8e6`](https://github.com/Hannes0730/Sticker-Hub/commit/73de8e67f22707ff3392e3155a65ef70e32a3065))


## v1.11.0 (2026-04-18)

### Documentation

- Add platform compatibility guide for sticker formats
  ([`6364239`](https://github.com/Hannes0730/Sticker-Hub/commit/63642391bed3ef8d5864012ea2a108bd58e97ce4))

### Features

- Enhance GIF saving with transparency support and frame processing
  ([`dff3997`](https://github.com/Hannes0730/Sticker-Hub/commit/dff3997102eabed9c2740cb0b5149878f4c9a5af))

### Refactoring

- Simplify copy format handling and remove compatibility mode
  ([`56ca6ab`](https://github.com/Hannes0730/Sticker-Hub/commit/56ca6ab4861e76966726411358540aa433ae1f2f))


## v1.10.0 (2026-04-18)

### Documentation

- Update README with usage instructions and delete actions
  ([`82c90cd`](https://github.com/Hannes0730/Sticker-Hub/commit/82c90cdb8c393e439e95a957b8a619c0f446871b))

### Features

- Add dedicated Stickerly provider for URL resolution
  ([`3bf78da`](https://github.com/Hannes0730/Sticker-Hub/commit/3bf78da2551c84ad27b421e3a0c6ca22cac4b01f))

- Add provider_generic module for improved functionality
  ([`c11f292`](https://github.com/Hannes0730/Sticker-Hub/commit/c11f2923f9ced05f7cea17feafd17355a6ef2b60))

- Add sigstick provider for image URL resolution
  ([`4303822`](https://github.com/Hannes0730/Sticker-Hub/commit/4303822c0473661c048ce4ee98b3152f4ce5b91b))

- Implement image URL extraction and normalization functionality
  ([`93b70f9`](https://github.com/Hannes0730/Sticker-Hub/commit/93b70f97753f6f6082ba04df945d607082834774))

### Refactoring

- Simplify sticker URL resolution by consolidating provider logic
  ([`dfc6dee`](https://github.com/Hannes0730/Sticker-Hub/commit/dfc6deefef7a2395bb5f7a787fe37287ea7e3f30))


## v1.9.0 (2026-04-18)

### Features

- Add delete functionality for sticker categories and packs
  ([`3dccd8d`](https://github.com/Hannes0730/Sticker-Hub/commit/3dccd8d0d018b7e5e91f2f5ceb167c67c9f8f5a1))

- Add delete functionality for sticker categories and packs from JSON
  ([`451334a`](https://github.com/Hannes0730/Sticker-Hub/commit/451334a4d0432c1bc7b1d4a82effa13755de9ad9))

- Add delete functionality for sticker packs and categories
  ([`d350096`](https://github.com/Hannes0730/Sticker-Hub/commit/d3500967aa33cd5da55df012910dfadd36ee17ee))


## v1.8.0 (2026-04-18)

### Bug Fixes

- Improve app version retrieval with error handling
  ([`d2cd56e`](https://github.com/Hannes0730/Sticker-Hub/commit/d2cd56e079e21208dfa58b640f8972ae09c03c9c))

### Features

- Add method to retrieve visible sticker cards from the grid
  ([`be90fdc`](https://github.com/Hannes0730/Sticker-Hub/commit/be90fdcffdd1c16faae89f1aab29b6bb538cd73e))

- Add pack filter and animation budget management to main window
  ([`806be50`](https://github.com/Hannes0730/Sticker-Hub/commit/806be502a5ab1960a2c96cb9ba45e8f19fa8fb5a))

- Enhance image URL handling with animated format detection
  ([`edb4519`](https://github.com/Hannes0730/Sticker-Hub/commit/edb45199caa5b0638692625a8c82b05e47942c2d))

- Enhance sticker card animation handling with state synchronization
  ([`d375606`](https://github.com/Hannes0730/Sticker-Hub/commit/d375606a728247f7424503f2b01fcbbcbe93a4b4))

- Enhance sticker parsing and storage with pack support
  ([`b875ae0`](https://github.com/Hannes0730/Sticker-Hub/commit/b875ae08709e2ea981fd04c9ebb504f48377499c))


## v1.7.2 (2026-04-18)

### Bug Fixes

- Update window title from 'Sticker Board' to 'Sticker Hub'
  ([`07593b9`](https://github.com/Hannes0730/Sticker-Hub/commit/07593b95350d5f1234f4f017d83ba0aa6d3fe9da))

### Chores

- Add MIT License file
  ([`28b9f97`](https://github.com/Hannes0730/Sticker-Hub/commit/28b9f97b79e6f0173991ea9f70f8e13c87fe4e9f))

### Documentation

- Update README to reflect app name change from 'Sticker Board' to 'Stickers Hub'
  ([`5a8d59b`](https://github.com/Hannes0730/Sticker-Hub/commit/5a8d59bc173ed0d625cf85d365ecf06cc8ffe473))


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
