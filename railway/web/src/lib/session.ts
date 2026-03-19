import { headers } from "next/headers";

export async function isSignedInRequest() {
  const requestHeaders = await headers();
  const status = requestHeaders.get("x-clerk-auth-status");
  return status === "signed-in";
}
