let MaxSpeed = 2;
let SpeedK = 0.8;
let PhysicsFPS = 10; 

class SpaceShipClass {
  constructor(Name, X, Y, SpeedX, SpeedY, Angle) { 
    this.Name = Name;
  	this.X = X; this.Y = Y;
  	this.SpeedX = SpeedX; this.SpeedY = SpeedY;
  	this.Angle = Angle;
  }
}

function sleep(milliseconds) {
  const date = Date.now();
  let currentDate = null;
  do {
    currentDate = Date.now();
  } while (currentDate - date < milliseconds);
}

SpaceShip = new SpaceShipClass("", 10, 10, 0, 0, 90);

document.addEventListener('keydown', (event) => {
  if(event.key === 'w' || event.key === 'ArrowUp') { SpaceShip.SpeedY = SpaceShip.SpeedY*SpeedK + MaxSpeed*(1-SpeedK); }  
  if(event.key === 'd' || event.key === 'ArrowRight') { SpaceShip.SpeedX = SpaceShip.SpeedX*SpeedK + MaxSpeed*(1-SpeedK); }

  if(event.key === 's' || event.key === 'ArrowDown') { SpaceShip.SpeedY = SpaceShip.SpeedY*SpeedK - MaxSpeed*(1-SpeedK); }
  if(event.key === 'a' || event.key === 'ArrowLeft') { SpaceShip.SpeedX = SpaceShip.SpeedX*SpeedK - MaxSpeed*(1-SpeedK); }

  //console.log(SpaceShip.SpeedY, SpaceShip.SpeedX);

  sleep(60/PhysicsFPS);
}, false);

function WhileTrue() {
  SpaceShip.X += SpaceShip.SpeedX;
  SpaceShip.Y += SpaceShip.SpeedY;
  sleep(60/PhysicsFPS);
  //console.log(SpaceShip.X, SpaceShip.Y);

  //document.getElementById("PlayerSpaceship").style.marginLeft = Math.round(SpaceShip.X).toString() + "px";
  //document.getElementById("PlayerSpaceship").style.maringTop = Math.round(SpaceShip.Y).toString() + "px";
}

setInterval(WhileTrue, 60/PhysicsFPS);