import "dotenv/config";

import express from "express";
import type { Request, Response } from "express";

import { paymentMiddleware } from "@x402/express";
import {
  HTTPFacilitatorClient,
  x402ResourceServer,
} from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import type { Network } from "@x402/core/types";

const app = express();

const port = Number(process.env.PORT ?? 4021);

const MONAD_NETWORK: Network = "eip155:10143";

const MONAD_USDC_TESTNET =
  "0x534b2f3A21130d7a60830c2Df862319e593943A3";

const FACILITATOR_URL =
  "https://x402-facilitator.molandak.org";

const payTo = process.env.PAY_TO_ADDRESS;

if (!payTo) {
  throw new Error(
    "PAY_TO_ADDRESS environment variable is required",
  );
}

app.use(express.json());

/*
 * Monad x402 configuration
 */

const facilitatorClient = new HTTPFacilitatorClient({
  url: FACILITATOR_URL,
});

const resourceServer =
  new x402ResourceServer(facilitatorClient);

const monadScheme = new ExactEvmScheme();

/*
 * Monad testnet USDC isn't in the SDK's built-in asset table,
 * so we register its money parser explicitly.
 */
monadScheme.registerMoneyParser(
  async (amount: string | number, network: string) => {
    if (network !== MONAD_NETWORK) {
      return null;
    }

    const numericAmount =
      typeof amount === "string"
        ? Number.parseFloat(amount)
        : amount;

    if (!Number.isFinite(numericAmount) || numericAmount < 0) {
      throw new Error(`Invalid payment amount: ${amount}`);
    }

    const tokenAmount = Math.floor(
      numericAmount * 1_000_000,
    ).toString();

    return {
      amount: tokenAmount,
      asset: MONAD_USDC_TESTNET,
      extra: {
        name: "USDC",
        version: "2",
      },
    };
  },
);

resourceServer.register(
  MONAD_NETWORK,
  monadScheme,
);

/*
 * Public endpoint.
 */
app.get(
  "/health",
  (_req: Request, res: Response) => {
    res.status(200).json({
      status: "ok",
      service: "agentmarket-api",
    });
  },
);

/*
 * Everything below this middleware is protected by x402.
 */
app.use(
  paymentMiddleware(
    {
      "GET /api/research": {
        accepts: {
          scheme: "exact",
          network: MONAD_NETWORK,
          payTo,
          price: "$0.001",
        },
        description:
          "AI-powered crypto market research",
        mimeType: "application/json",
      },
    },
    resourceServer,
  ),
);

/*
 * Paid endpoint.
 */
app.get(
  "/api/research",
  (_req: Request, res: Response) => {
    res.status(200).json({
      service: "research-agent",

      result: {
        asset: "ETH",
        sentiment: "bullish",
        confidence: 0.82,
      },

      purchasedAt: new Date().toISOString(),
    });
  },
);

app.listen(port, () => {
  console.log(
    `AgentMarket API running on http://localhost:${port}`,
  );
});