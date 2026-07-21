"""Verificacao de tokens Bearer: chaves estaticas ou JWT via IdP externo.

Implementa `mcp.server.auth.provider.TokenVerifier` combinando duas fontes de
confianca para o mesmo endpoint MCP:

1. Chaves estaticas pre-compartilhadas (`MCP_API_KEYS`) -- caminho rapido, sem
   chamada de rede, mesmo comportamento de sempre para clientes ja
   configurados manualmente (Antigravity, scripts).
2. JWT emitido por um authorization server externo (ex.: WorkOS AuthKit),
   validado localmente via JWKS (assinatura RS256 + `iss`/`aud`/`exp`) --
   necessario para clientes que fazem o fluxo OAuth 2.1 completo (ex.: o
   conector remoto do claude.ai).

Este servidor atua apenas como *resource server*: nao implementa `/authorize`,
`/token` nem `/register` -- a emissao de tokens e responsabilidade do IdP
externo configurado via `OAUTH_ISSUER_URL`.
"""

from __future__ import annotations

import jwt
import requests
from jwt import PyJWKClient
from mcp.server.auth.provider import AccessToken, TokenVerifier


def _discover_oidc_config(issuer_url: str) -> tuple[str, str]:
    """Descobre `issuer` e `jwks_uri` via OpenID Connect Discovery
    (`{issuer}/.well-known/openid-configuration`), o mecanismo padrao
    suportado por qualquer IdP compativel (WorkOS, Auth0, etc.) -- evita
    hardcodar a convencao de path de um provedor especifico.

    Usa o `issuer` retornado pelo proprio IdP (nao uma normalizacao nossa)
    para validar o claim `iss` dos tokens: IdPs divergem sobre incluir
    barra final (WorkOS nao inclui, Auth0 inclui) -- confiar no valor
    auto-declarado evita mismatch silencioso.
    """
    discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    response = requests.get(discovery_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["issuer"], data["jwks_uri"]


class JWTBearerTokenVerifier(TokenVerifier):
    def __init__(
        self,
        valid_tokens: set[str],
        issuer_url: str,
        audience: str,
        jwks_url: str | None = None,
    ) -> None:
        self._valid_tokens = valid_tokens
        self._audience = audience
        if jwks_url:
            # jwks_url explicito: nao ha discovery para nos dar o `issuer`
            # auto-declarado, entao normalizamos barra final por conta propria.
            self._issuer_url = issuer_url.rstrip("/")
            resolved_jwks_url = jwks_url
        else:
            self._issuer_url, resolved_jwks_url = _discover_oidc_config(issuer_url)
        self._jwk_client = PyJWKClient(resolved_jwks_url)

    async def verify_token(self, token: str) -> AccessToken | None:
        if token in self._valid_tokens:
            return AccessToken(
                token=token,
                client_id="static-api-key",
                scopes=["*"],
                resource=self._audience,
            )

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer_url,
            )
        except jwt.PyJWTError:
            return None

        scopes_raw = claims.get("scope") or claims.get("scopes") or ""
        scopes = scopes_raw.split() if isinstance(scopes_raw, str) else list(scopes_raw)

        return AccessToken(
            token=token,
            client_id=claims.get("client_id") or claims.get("azp") or "unknown",
            scopes=scopes,
            expires_at=claims.get("exp"),
            resource=self._audience,
            subject=claims.get("sub"),
            claims=claims,
        )
