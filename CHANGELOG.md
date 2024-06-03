# Changelog

## [0.2.2](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.2.1...v0.2.2) (2024-06-03)


### 🐛 Bug Fixes

* Add readme for confidence flag api ([#53](https://github.com/spotify/confidence-openfeature-provider-python/issues/53)) ([f840603](https://github.com/spotify/confidence-openfeature-provider-python/commit/f840603616953b1b3d551b950aa2a689023d99bf))
* run async io task in the background ([#55](https://github.com/spotify/confidence-openfeature-provider-python/issues/55)) ([e7c87bd](https://github.com/spotify/confidence-openfeature-provider-python/commit/e7c87bdfb72e5f1b62ae5cbcf1d813eb965b7797))

## [0.2.1](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.2.0...v0.2.1) (2024-05-29)


### 🐛 Bug Fixes

* Change the artifact name for the library to confidence-sdk ([#51](https://github.com/spotify/confidence-openfeature-provider-python/issues/51)) ([6ad000f](https://github.com/spotify/confidence-openfeature-provider-python/commit/6ad000f22f793f8b263f710bf6918ea71adfeaa3))

## [0.2.0](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.1.4...v0.2.0) (2024-05-29)


### ⚠ BREAKING CHANGES

* total confidence ([#49](https://github.com/spotify/confidence-openfeature-provider-python/issues/49))

### ✨ New Features

* total confidence ([#49](https://github.com/spotify/confidence-openfeature-provider-python/issues/49)) ([58437a3](https://github.com/spotify/confidence-openfeature-provider-python/commit/58437a355b4cad235b61b9a61c7b0131ad926c55))

## [0.1.4](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.1.3...v0.1.4) (2024-02-13)


### 🐛 Bug Fixes

* add a default endpoint to the provider ([#46](https://github.com/spotify/confidence-openfeature-provider-python/issues/46)) ([1f30ef7](https://github.com/spotify/confidence-openfeature-provider-python/commit/1f30ef7583939967407f11fbeb797c07bb06d9f3))
* fixes to enable mypy in premerge ([#42](https://github.com/spotify/confidence-openfeature-provider-python/issues/42)) ([c1d65bf](https://github.com/spotify/confidence-openfeature-provider-python/commit/c1d65bf3a7338cee920ce3936e2bcbc6a98e4095))


### 🧹 Chore
* update OF sdk to 0.4.2 ([dd4a4d7](https://github.com/spotify/confidence-openfeature-provider-python/commit/dd4a4d74cb91331ce6768ef12ee08b14b89c7eac)

* explicitly add the typing-extensions dep ([49ac4eb](https://github.com/spotify/confidence-openfeature-provider-python/commit/49ac4ebbb23fa28f1f6d69b6fea29e000ef63759))

* update openfeature sdk version to 0.4.1 ([#35](https://github.com/spotify/confidence-openfeature-provider-python/issues/35)) ([16ee55f](https://github.com/spotify/confidence-openfeature-provider-python/commit/16ee55f804b3a488926647a697cf37a4bf25af69))


### 📚 Documentation

* Add Confidence link to the README ([#44](https://github.com/spotify/confidence-openfeature-provider-python/issues/44)) ([bee1d17](https://github.com/spotify/confidence-openfeature-provider-python/commit/bee1d175a0478abc18a196d3bd2f48ffe8ab0005))

## [0.1.3](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.1.2...v0.1.3) (2023-11-16)


### 🐛 Bug Fixes

* check types with mypy ([#31](https://github.com/spotify/confidence-openfeature-provider-python/issues/31)) ([e6d4dcd](https://github.com/spotify/confidence-openfeature-provider-python/commit/e6d4dcd664971935905dc58d0681ecc46b0063de))


### ✨ New Features

* Add SDK id and version to requests ([#34](https://github.com/spotify/confidence-openfeature-provider-python/issues/34)) ([6c82014](https://github.com/spotify/confidence-openfeature-provider-python/commit/6c82014717feaa4a13db9397cbdf7ff71e504c17))

## [0.1.2](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.1.1...v0.1.2) (2023-10-09)


### 🐛 Bug Fixes

* update to openfeature 0.3.1 and fix some type issues ([#29](https://github.com/spotify/confidence-openfeature-provider-python/issues/29)) ([6c0c5b1](https://github.com/spotify/confidence-openfeature-provider-python/commit/6c0c5b11194d614aea93e661ad28c11c2b54b627))

## [0.1.1](https://github.com/spotify/confidence-openfeature-provider-python/compare/v0.1.0...v0.1.1) (2023-09-18)


### 🐛 Bug Fixes

* make _select a static method ([#22](https://github.com/spotify/confidence-openfeature-provider-python/issues/22)) ([0ad2b88](https://github.com/spotify/confidence-openfeature-provider-python/commit/0ad2b8863adaf9b8ade87d7504d461737763693f))


### 📚 Documentation

* update CONTRIBUTING.md ([#26](https://github.com/spotify/confidence-openfeature-provider-python/issues/26)) ([b574341](https://github.com/spotify/confidence-openfeature-provider-python/commit/b57434152e914768e16191195f36f059fb3a929a))

## 0.1.0 (2023-09-14)


### 🐛 Bug Fixes

* allow omitting targeting key ([#17](https://github.com/spotify/confidence-openfeature-provider-python/issues/17)) ([ddb535f](https://github.com/spotify/confidence-openfeature-provider-python/commit/ddb535fb197fa958d42d33a540de6a8c3b5c5f00))
* int syntax error in resolver ([#14](https://github.com/spotify/confidence-openfeature-provider-python/issues/14)) ([5e4dcdd](https://github.com/spotify/confidence-openfeature-provider-python/commit/5e4dcddee5a4a053a266fff6f1ce46a445907a86))
* make resolve payload have appended "flags/" ([#18](https://github.com/spotify/confidence-openfeature-provider-python/issues/18)) ([97c6f9a](https://github.com/spotify/confidence-openfeature-provider-python/commit/97c6f9a0faf7c5d894fc540e0d415cd2cf248f7a))


### ✨ New Features

* make apply on resolve configurable. ([#7](https://github.com/spotify/confidence-openfeature-provider-python/issues/7)) ([50a06a8](https://github.com/spotify/confidence-openfeature-provider-python/commit/50a06a89e30443a5c994581081b9e0a82e86ec18)), closes [#2](https://github.com/spotify/confidence-openfeature-provider-python/issues/2)


### 🧹 Chore

* test to start from 0 ([f67395f](https://github.com/spotify/confidence-openfeature-provider-python/commit/f67395f7005642da78a8107e702ad32c5976bdca))


### 📦 Dependencies

* bump to openfeature sdk v0.2.0 ([#12](https://github.com/spotify/confidence-openfeature-provider-python/issues/12)) ([2f8b8a6](https://github.com/spotify/confidence-openfeature-provider-python/commit/2f8b8a600abe0719fb2aa6fc9389b6f2257ee07f))


### 🔄 Refactoring

* module restructure ([#15](https://github.com/spotify/confidence-openfeature-provider-python/issues/15)) ([341577a](https://github.com/spotify/confidence-openfeature-provider-python/commit/341577ab450a8f182de3802ba62a2a2f0551601d))
