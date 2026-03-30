import process from "node:process";

const requiredEnv = (name) => {
  const value = process.env[name];

  if (!value) {
    throw new Error(`${name} is required`);
  }

  return value;
};

export const appConfig = {
  bind: "0.0.0.0",
  port: 8080,
  serviceName: "app1",
  service2BaseUrl: requiredEnv("SERVICE2_BASE_URL"),
};
