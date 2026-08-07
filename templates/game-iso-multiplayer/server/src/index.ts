// Arranque del servidor Colyseus. Define la sala "hotel". El cliente conecta por
// ws://localhost:2567 (VITE_SERVER_URL). El monitor de Colyseus queda en /colyseus.
import { createServer } from "http";
import express from "express";
import { Server } from "colyseus";
import { monitor } from "@colyseus/monitor";
import { HotelRoom } from "./HotelRoom.js";

const app = express();
app.use(express.json());
app.use("/colyseus", monitor());          // panel de salas (dev)
app.get("/health", (_req, res) => res.json({ ok: true }));

const httpServer = createServer(app);
const gameServer = new Server({ server: httpServer });
gameServer.define("hotel", HotelRoom);

const PORT = Number(process.env.PORT ?? 2567);
gameServer.listen(PORT);
console.log(`[server] Colyseus escuchando en ws://localhost:${PORT}  ·  monitor http://localhost:${PORT}/colyseus`);
