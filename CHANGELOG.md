# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-21

### Added

- Initial release of `squidrouter-py`.
- Synchronous `SquidClient` and asynchronous `AsyncSquidClient`, built on
  `httpx` and `pydantic` v2.
- Required `integrator_id` argument, sent in the configurable `x-integrator-id`
  header.
- Endpoint methods: `get_chains`, `get_tokens`, `get_route`, `get_status`.
- `poll_status` helper that polls until a terminal cross-chain state.
- Typed pydantic models for requests and responses
  (`RouteRequest`, `RouteResponse`, `Route`, `Estimate`, `TransactionRequest`,
  `StatusResponse`, `Chain`, `ChainsResponse`, `Token`, `TokensResponse`).
- Exception hierarchy: `SquidError`, `SquidAPIError`, `StatusTimeoutError`.
- `py.typed` marker for downstream type checking.

[Unreleased]: https://github.com/robertruben98/squidrouter-py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/robertruben98/squidrouter-py/releases/tag/v0.1.0
