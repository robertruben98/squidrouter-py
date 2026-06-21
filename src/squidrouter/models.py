"""Pydantic models for Squid Router API requests and responses.

The Squid Router API returns large, frequently-evolving JSON payloads. To stay
forward-compatible, response models permit extra fields (``extra="allow"``) and
type only the documented attributes. Unknown fields remain accessible via normal
attribute access on the parsed model.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class SquidModel(BaseModel):
    """Base model for permissive, forward-compatible Squid API responses."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class RouteRequest(BaseModel):
    """Parameters for a cross-chain route request (``POST /v2/route``).

    Attributes:
        from_chain: Source chain ID (e.g. ``"56"`` for BNB Chain). Sent as
            ``fromChain``.
        from_token: Source token contract address. Sent as ``fromToken``.
        from_amount: Amount to swap, in the token's smallest unit (wei-style
            integer string). Sent as ``fromAmount``.
        to_chain: Destination chain ID (e.g. ``"42161"`` for Arbitrum). Sent as
            ``toChain``.
        to_token: Destination token contract address. Sent as ``toToken``.
        from_address: Address initiating the swap. Sent as ``fromAddress``.
        to_address: Address receiving the swapped tokens. Sent as ``toAddress``.
        slippage: Maximum acceptable slippage as a percentage (e.g. ``1.0`` for
            1%). Optional.
        slippage_config: Advanced slippage configuration object, sent as
            ``slippageConfig`` when provided.
        enable_boost: Whether to enable Squid Boost for faster settlement. Sent
            as ``enableBoost``.
        quote_only: When ``True``, returns a quote without a signable
            ``transactionRequest``. Sent as ``quoteOnly``.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    from_chain: str = Field(serialization_alias="fromChain", description="Source chain ID.")
    from_token: str = Field(
        serialization_alias="fromToken", description="Source token contract address."
    )
    from_amount: str = Field(
        serialization_alias="fromAmount",
        description="Amount to swap, in the token's smallest unit.",
    )
    to_chain: str = Field(serialization_alias="toChain", description="Destination chain ID.")
    to_token: str = Field(
        serialization_alias="toToken", description="Destination token contract address."
    )
    from_address: str = Field(
        serialization_alias="fromAddress", description="Address initiating the swap."
    )
    to_address: str = Field(
        serialization_alias="toAddress", description="Address receiving the swapped tokens."
    )
    slippage: Optional[float] = Field(
        default=None, description="Maximum acceptable slippage, as a percentage."
    )
    slippage_config: Optional[dict[str, Any]] = Field(
        default=None,
        serialization_alias="slippageConfig",
        description="Advanced slippage configuration object.",
    )
    enable_boost: Optional[bool] = Field(
        default=None,
        serialization_alias="enableBoost",
        description="Enable Squid Boost for faster settlement.",
    )
    quote_only: Optional[bool] = Field(
        default=None,
        serialization_alias="quoteOnly",
        description="Return a quote without a signable transactionRequest.",
    )

    def to_payload(self) -> dict[str, Any]:
        """Serialize to the JSON body expected by ``POST /v2/route``.

        Returns:
            A dict using the API's camelCase field names, omitting unset
            optional values.
        """
        return self.model_dump(by_alias=True, exclude_none=True)


class TransactionRequest(SquidModel):
    """An on-chain transaction to execute a route.

    Attributes:
        target: Contract address to send the transaction to. Some responses use
            ``targetAddress`` instead; both are accepted.
        data: Calldata for the transaction.
        value: Native token value to send, as a string.
        gas_limit: Suggested gas limit, sent by the API as ``gasLimit``.
        gas_price: Suggested gas price, sent by the API as ``gasPrice``.
    """

    target: Optional[str] = Field(default=None, description="Contract address to call.")
    data: Optional[str] = Field(default=None, description="Transaction calldata.")
    value: Optional[str] = Field(default=None, description="Native value to send.")
    gas_limit: Optional[str] = Field(
        default=None, alias="gasLimit", description="Suggested gas limit."
    )
    gas_price: Optional[str] = Field(
        default=None, alias="gasPrice", description="Suggested gas price."
    )


class Estimate(SquidModel):
    """Estimated outcome of a route.

    Attributes:
        to_amount: Estimated amount received at the destination, as a string.
        to_amount_min: Minimum guaranteed amount after slippage, as a string.
        fee_costs: List of fee breakdown objects.
        gas_costs: List of gas cost breakdown objects.
        estimated_route_duration: Estimated route duration in seconds.
    """

    to_amount: Optional[str] = Field(
        default=None, alias="toAmount", description="Estimated amount received."
    )
    to_amount_min: Optional[str] = Field(
        default=None, alias="toAmountMin", description="Minimum amount after slippage."
    )
    fee_costs: Optional[list[dict[str, Any]]] = Field(
        default=None, alias="feeCosts", description="Fee breakdown."
    )
    gas_costs: Optional[list[dict[str, Any]]] = Field(
        default=None, alias="gasCosts", description="Gas cost breakdown."
    )
    estimated_route_duration: Optional[Union[int, float]] = Field(
        default=None,
        alias="estimatedRouteDuration",
        description="Estimated route duration in seconds.",
    )


class Route(SquidModel):
    """A single cross-chain route returned by ``POST /v2/route``.

    Attributes:
        estimate: The estimated outcome of executing this route.
        transaction_request: The signable transaction for this route, sent by
            the API as ``transactionRequest``. Absent for quote-only requests.
        quote_id: Identifier for this quote, sent as ``quoteId``. Must be passed
            to the status endpoint for Squid Intents transactions.
        params: Echo of the route parameters used to compute this route.
    """

    estimate: Optional[Estimate] = Field(default=None, description="Estimated route outcome.")
    transaction_request: Optional[TransactionRequest] = Field(
        default=None,
        alias="transactionRequest",
        description="Signable transaction for this route.",
    )
    quote_id: Optional[str] = Field(
        default=None, alias="quoteId", description="Quote identifier for status tracking."
    )
    params: Optional[dict[str, Any]] = Field(
        default=None, description="Echo of the route parameters."
    )


class RouteResponse(SquidModel):
    """Top-level response for ``POST /v2/route``.

    Attributes:
        route: The computed route, including estimate and transaction request.
        request_id: The ``x-request-id`` response header value, populated by the
            client. Required (with ``quote_id``) for status tracking.
    """

    route: Optional[Route] = Field(default=None, description="The computed cross-chain route.")
    request_id: Optional[str] = Field(
        default=None,
        alias="requestId",
        description="x-request-id response header, populated by the client.",
    )


class StatusResponse(SquidModel):
    """Response for ``GET /v2/status``.

    Attributes:
        squid_transaction_status: Overall status of the cross-chain transaction.
            Terminal values include ``success``, ``partial_success``,
            ``needs_gas`` and ``not_found``. Sent as ``squidTransactionStatus``.
        status: A finer-grained status string, when provided by the API.
        id: The transaction identifier echoed by the API.
        from_chain: Source-chain status object.
        to_chain: Destination-chain status object.
    """

    squid_transaction_status: Optional[str] = Field(
        default=None,
        alias="squidTransactionStatus",
        description="Overall cross-chain transaction status.",
    )
    status: Optional[str] = Field(default=None, description="Finer-grained status string.")
    id: Optional[str] = Field(default=None, description="Transaction identifier.")
    from_chain: Optional[dict[str, Any]] = Field(
        default=None, alias="fromChain", description="Source-chain status."
    )
    to_chain: Optional[dict[str, Any]] = Field(
        default=None, alias="toChain", description="Destination-chain status."
    )


class Chain(SquidModel):
    """A chain supported by Squid Router (``GET /v2/chains``).

    Attributes:
        chain_id: The chain's identifier, sent as ``chainId``. May be an int or
            string depending on the chain type.
        chain_name: Human-readable chain name, sent as ``chainName``.
        chain_type: The chain family (e.g. ``evm``, ``cosmos``), sent as
            ``chainType``.
        network_name: The network name, sent as ``networkName``.
        rpc: The default RPC endpoint for the chain.
    """

    chain_id: Optional[Union[int, str]] = Field(
        default=None, alias="chainId", description="Chain identifier."
    )
    chain_name: Optional[str] = Field(
        default=None, alias="chainName", description="Human-readable chain name."
    )
    chain_type: Optional[str] = Field(
        default=None, alias="chainType", description="Chain family (evm, cosmos, ...)."
    )
    network_name: Optional[str] = Field(
        default=None, alias="networkName", description="Network name."
    )
    rpc: Optional[str] = Field(default=None, description="Default RPC endpoint.")


class ChainsResponse(SquidModel):
    """Response for ``GET /v2/chains``.

    Attributes:
        chains: The list of supported chains.
    """

    chains: list[Chain] = Field(default_factory=list, description="Supported chains.")


class Token(SquidModel):
    """A token supported by Squid Router (``GET /v2/tokens``).

    Attributes:
        symbol: The token's ticker symbol.
        name: The token's display name.
        address: The token's contract address.
        decimals: The token's decimal precision.
        chain_id: The chain the token lives on, sent as ``chainId``.
        coingecko_id: The CoinGecko identifier, sent as ``coingeckoId``.
        logo_uri: A URI to the token logo, sent as ``logoURI``.
    """

    symbol: Optional[str] = Field(default=None, description="Token ticker symbol.")
    name: Optional[str] = Field(default=None, description="Token display name.")
    address: Optional[str] = Field(default=None, description="Token contract address.")
    decimals: Optional[int] = Field(default=None, description="Token decimal precision.")
    chain_id: Optional[Union[int, str]] = Field(
        default=None, alias="chainId", description="Chain the token lives on."
    )
    coingecko_id: Optional[str] = Field(
        default=None, alias="coingeckoId", description="CoinGecko identifier."
    )
    logo_uri: Optional[str] = Field(
        default=None, alias="logoURI", description="URI to the token logo."
    )


class TokensResponse(SquidModel):
    """Response for ``GET /v2/tokens``.

    Attributes:
        tokens: The list of supported tokens.
    """

    tokens: list[Token] = Field(default_factory=list, description="Supported tokens.")
