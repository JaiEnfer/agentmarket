import "dotenv/config";

import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client } from "@x402/core/client";
import { ExactEvmScheme } from "@x402/evm";

const MONAD_NETWORK = "eip155:10143" as const;
const MONAD_USDC_TESTNET =
  "0x534b2f3A21130d7a60830c2Df862319e593943A3";

const privateKey = process.env.PRIVATE_KEY;
const apiUrl =
  process.env.AGENTMARKET_API_URL ??
  "http://localhost:4021/api/research";

if (!privateKey) {
  throw new Error("PRIVATE_KEY environment variable is required");
}

if (!/^0x[a-fA-F0-9]{64}$/.test(privateKey)) {
  throw new Error("PRIVATE_KEY is not a valid EVM private key");
}

const account = privateKeyToAccount(
  privateKey as `0x${string}`,
);

/*
 * Adapter expected by ExactEvmScheme.
 *
 * The private key never leaves this process.
 * Only EIP-712 payment authorization is signed.
 */
const signer = {
  address: account.address,

  signTypedData: async (message: {
    domain: Record<string, unknown>;
    types: Record<string, unknown>;
    primaryType: string;
    message: Record<string, unknown>;
  }) =>
    account.signTypedData({
      domain: message.domain as Parameters<
        typeof account.signTypedData
      >[0]["domain"],

      types: message.types as Parameters<
        typeof account.signTypedData
      >[0]["types"],

      primaryType: message.primaryType,

      message: message.message,
    }),
};

const scheme = new ExactEvmScheme(signer);

const client = x402Client.fromConfig({
  schemes: [
    {
      network: MONAD_NETWORK,
      client: scheme,
    },
  ],
  spendControls: {
    allowedAssets: [
      {
        network: MONAD_NETWORK,
        asset: MONAD_USDC_TESTNET,
        maxAmountPerPayment: "1000",
      },
    ],
  },
});

const paymentFetch = wrapFetchWithPayment(
  fetch,
  client,
);

async function main(): Promise<void> {

  const response = await paymentFetch(apiUrl, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  const body = await response.text();

  if (!response.ok) {
    throw new Error(
      `Paid request failed: HTTP ${response.status}\n${body}`,
    );
  }

  const purchasedData = JSON.parse(body);

  console.log(
    JSON.stringify({
      success: true,
      status: response.status,
      network: MONAD_NETWORK,
      amount: "0.001",
      currency: "USDC",
      payer: account.address,
      data: purchasedData,
    }),
  );
}

main().catch((error: unknown) => {
  const message =
    error instanceof Error
      ? error.message
      : String(error);

  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});