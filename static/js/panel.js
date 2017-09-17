// Initialize Firebase
var config = {
  apiKey: "AIzaSyDTYAGexqXARKksJyCyVmfqpQvDWf7wbJ0",
  authDomain: "panel-180102.firebaseapp.com",
  databaseURL: "https://panel-180102.firebaseio.com",
  projectId: "panel-180102",
  storageBucket: "panel-180102.appspot.com",
  messagingSenderId: "291322636234"
};

firebase.initializeApp(config);

var storageRef = firebase.storage().ref();
var database = firebase.database();

function startGrid() {

    counter = 1;

    database.ref('images').on('child_added', function(childSnapshot, prevChildName) {

      populateGrid(childSnapshot.key, counter);

      if (counter == 24 ) {
        counter = 1;
      }

      else {
        counter++;
      }

    });
}

function populateGrid(imageName, gridPos) {

  storageRef.child('gifs/' + imageName + '.gif').getDownloadURL().then(function(url) {

    var img = document.getElementById('square-' + gridPos);
    img.src = url;
  }).catch(function(error) {

  });

}
