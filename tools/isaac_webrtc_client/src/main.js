import { AppStreamer, StreamType } from "@nvidia/ov-web-rtc";
import "./styles.css";

const params = new URLSearchParams(window.location.search);
const server = params.get("server") || window.location.hostname || "localhost";
const signalingPort = Number(params.get("signalingport") || params.get("port") || 49100);

const statusEl = document.getElementById("status");
const endpointEl = document.getElementById("endpoint");
endpointEl.textContent = `${server}:${signalingPort}`;

function setStatus(text, tone = "pending") {
  statusEl.textContent = text;
  statusEl.dataset.tone = tone;
}

const config = {
  videoElementId: "remote-video",
  audioElementId: "remote-audio",
  server,
  signalingPort,
  nativeTouchEvents: true,
  fps: 60,
  maxReconnects: 5,
  reconnectDelay: 3000,
  onStart: () => setStatus("connected", "ok"),
  onUpdate: () => setStatus("streaming", "ok"),
  onStop: () => setStatus("stopped", "warn"),
  onTerminate: () => setStatus("terminated", "warn"),
  onCustomEvent: () => undefined,
};

setStatus("connecting", "pending");

AppStreamer.connect({
  streamSource: StreamType.DIRECT,
  streamConfig: config,
}).catch((error) => {
  console.error(error);
  setStatus(error?.message || "connection failed", "error");
});
