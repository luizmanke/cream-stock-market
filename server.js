// System libraries
const bodyParser = require("body-parser");
const express = require("express");

// Own libraries
const databaseRoute = require("./backend/routes/database");

// Configurations
const port = process.env.PORT || 5000;

// Create server
const server = express();

// Middlewares
server.use(bodyParser.json());
server.use("/database", databaseRoute);

// Hello world
server.get("/", (req, res) => {
  res.json({ message: "Hello world!" });
});

// Start server
var serverObject = server.listen(port, () => {
  console.log(`Server running on port ${port}...`);
});
serverObject.timeout = 1200000;