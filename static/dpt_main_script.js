function autocomplete(inp, arr) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) { return false;}
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        /*for each item in the array...*/
        for (i = 0; i < arr.length; i++) {
          /*check if the item starts with the same letters as the text field value:*/
          if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
            /*create a DIV element for each matching element:*/
            b = document.createElement("DIV");
            /*make the matching letters bold:*/
            b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
            b.innerHTML += arr[i].substr(val.length);
            /*insert a input field that will hold the current array item's value:*/
            b.innerHTML += '<input type="hidden" value="' + arr[i] + '">';
            /*execute a function when someone clicks on the item value (DIV element):*/
            b.addEventListener("click", function(e) {
                /*insert the value for the autocomplete text field:*/
                inp.value = this.getElementsByTagName("input")[0].value;
                /*close the list of autocompleted values,
                (or any other open lists of autocompleted values:*/
                closeAllLists();
            });
            a.appendChild(b);
          }
        }
    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
          /*If the arrow DOWN key is pressed,
          increase the currentFocus variable:*/
          currentFocus++;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 38) { //up
          /*If the arrow UP key is pressed,
          decrease the currentFocus variable:*/
          currentFocus--;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 13) {
          /*If the ENTER key is pressed, prevent the form from being submitted,*/
          e.preventDefault();
          if (currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (x) x[currentFocus].click();
          }
        }
    });
    function addActive(x) {
      /*a function to classify an item as "active":*/
      if (!x) return false;
      /*start by removing the "active" class on all items:*/
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      /*add class "autocomplete-active":*/
      x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
      /*a function to remove the "active" class from all autocomplete items:*/
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }
    function closeAllLists(elmnt) {
      /*close all autocomplete lists in the document,
      except the one passed as an argument:*/
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }
  /*execute a function when someone clicks in the document:*/
  document.addEventListener("click", function (e) {
      closeAllLists(e.target);
  });
  }


  function submissionLogic(btn, dpt_fields, dpt_row, dpt_field_question, start_time_str, baseUrl) {
    btn.addEventListener("click", function()  {

      // set layout of answers div
      answersDiv = document.getElementById("display-answers")
      answersDiv.className = "display-answers"

      // loop over all fields
      const ajaxPayload = {}
      let i = 1
      for (let dpt_field of dpt_fields) {

        // display answer for all fileds except questionned field
        if (dpt_field_question !== dpt_field) {
          
          // 1- freeze user answer
          console.log(dpt_field + '-input')
          let userAnswerElt = document.getElementById(dpt_field + '-input');
          userAnswerElt.readOnly = true;

          // 2- display correct answers

          // prepare answer span
          let actualAnswer = dpt_row[dpt_field]
          let answerElt = document.createElement("span")
          answerElt.id = dpt_field + '-answer'
          answerElt.innerHTML = actualAnswer

          // color answer in green if correct answer and in red otherwise
          let userAnswer = userAnswerElt.value
          if (actualAnswer === userAnswer) {
            answerElt.setAttribute("style", "color:green;");
          } else {
            answerElt.setAttribute("style", "color:red;");
          }
          answersDiv.appendChild(answerElt)

          // add separators between answers except if last answer
          if (i < (dpt_fields.length - 1)) {
            let sep = document.createElement("span")
            sep.innerHTML = ' - '
            answersDiv.appendChild(sep)
          }
          i += 1

          // 3- update scores
          let scoreElt = document.getElementById(dpt_field + '-score')
          let currentScore = scoreElt.getElementsByClassName('current-score')[0]
          let totalAnswers = scoreElt.getElementsByClassName('total-answers')[0]
          if (actualAnswer === userAnswer) {
            currentScore.innerHTML = parseInt(currentScore.innerHTML) + 1
          }
          totalAnswers.innerHTML = parseInt(totalAnswers.innerHTML) + 1
          ajaxPayload[dpt_field + '_score'] = parseInt(currentScore.innerHTML)
          ajaxPayload['total_answers'] = totalAnswers.innerHTML // overwritted each time
        }
      }
      let remainingQuestionsElt = document.getElementById('remaining-questions-value')
      console.log(remainingQuestionsElt)
      console.log(parseInt(remainingQuestionsElt.innerHTML) - 1)
      if (parseInt(remainingQuestionsElt.innerHTML) > 0) {
        remainingQuestionsElt.innerHTML = parseInt(remainingQuestionsElt.innerHTML) - 1
      }

      // replace validation button with next button
      btn.hidden = true
      document.getElementById("next-button").hidden = false

      // calculate game duratin (for payload and UI)
      const endTime = new Date()
      const endTimeStr = endTime.toISOString().replaceAll('T', ' ').split('.')[0]
      ajaxPayload['training_end_time'] = endTimeStr

      const elapsedTimeElt = document.getElementById('elapsed-time-value')
      displayElapsedTime(elapsedTimeElt, start_time_str)
      ajaxPayload['training_duration'] = elapsedTimeElt.innerHTML

      console.log(ajaxPayload)

      // AJAX POST request to update db with latest status
      const xhr = new XMLHttpRequest();
      xhr.open('POST', baseUrl + '/update_scores', true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(JSON.stringify(ajaxPayload));

      // Response handling
      xhr.onload = function() {
        if (xhr.status === 200) {
          // Handle success
          console.log('Scores updated successfully in DB');
        } else {
          // Handle error
          console.error('Error updating scores');
        }
      };

    });
  }


  function generateScoreTable(scoreBoardColumns, scoreBoardData, gameMode, rankingMode) {

    const table = document.getElementById('score-table-content')
    table.innerHTML = ''

    // filter scores to keep only relevant game mode
    const scoreBoardDataFiltered = scoreBoardData.filter(scoreRow => scoreRow['game_mode'] === gameMode.replaceAll('-mode', ''))

    // calculate duration int +  + modify start time string
    const scoreBoardDataForSorting = []
    for (let scoreRow of scoreBoardDataFiltered) {
      const scoreRowModified = {...scoreRow}
      // change game mode format for better display
      scoreRowModified['game_mode'] = scoreRowModified['game_mode'].replaceAll('_departement', '')
      // convert utc datetime string to locale datetime string
      scoreRowModified['training_start_time'] = (new Date(Date.parse(scoreRowModified['training_start_time']))).toLocaleString('fr-FR')
      // calculate game duration as int for sorting
      const trainDurationArray = scoreRow.training_duration.split(':')
      const trainingDurationInt = (
        parseInt(trainDurationArray[2])
        + parseInt(trainDurationArray[1]) * 60
        + parseInt(trainDurationArray[0]) * 3600)
        scoreBoardDataForSorting.push({...scoreRowModified, ...{'training_duration_int': trainingDurationInt}})
    }

    // adjust the ranking mode format to match object key, and then filter
    const rankingModeAdjusted = rankingMode.replaceAll('-ranking', '_score').replaceAll('general', 'total')
    scoreBoardDataForSorting.sort(
      (scoreRowA, scoreRowB) => (
        scoreRowB[rankingModeAdjusted] - scoreRowA[rankingModeAdjusted])
        || scoreRowA.training_duration_int - scoreRowB.training_duration_int)
    
    
    for (let scoreRowData of scoreBoardDataForSorting) {
      const row = table.insertRow(-1);
      let i = 0
      for (let tableCol of scoreBoardColumns) {
        const cell = row.insertCell(i)
        cell.innerHTML = scoreRowData[tableCol]
        if (tableCol === rankingModeAdjusted) {
          cell.className = 'ranking-col'
        }
        i ++
      }
    }

  }



  function selectGameMode(evt, selectedGameMode, scoreBoardColumns, scoreBoardData) {
    // Declare all variables
  
    // Get all elements with class="tablinks" and remove the class "active"
    const tablinks = document.getElementById("tabs-game-mode").getElementsByClassName("tab-links");
    for (let i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
  
    // Show the current tab, and add an "active" class to the button that opened the tab
    console.log('selectedGameMode: ' + selectedGameMode)
    gameMode = selectedGameMode
    evt.currentTarget.className += " active";

    generateScoreTable(scoreBoardColumns, scoreBoardData, gameMode, rankingMode)
  }



  function selectRankingMode(evt, selectedRankingMode, scoreBoardColumns, scoreBoardData) {
    // Declare all variables

    // Get all elements with class="tablinks" and remove the class "active"
    const tablinks = document.getElementById("tabs-ranking-mode").getElementsByClassName("tab-links");
    for (let i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
  
    // Show the current tab, and add an "active" class to the button that opened the tab
    console.log('selectedRankingMode: ' + selectedRankingMode)
    rankingMode = selectedRankingMode
    evt.currentTarget.className += " active";

    generateScoreTable(scoreBoardColumns, scoreBoardData, gameMode, rankingMode)
  }



  function displayElapsedTime(elt, startTimeStr) {
    const startTime = Date.parse(startTimeStr)
    const endTime = Date.now()
    console.log(startTime)
    console.log(endTime)

    const diff = {}
    let tmp = endTime - startTime;

    console.log(tmp)
  
    tmp = Math.floor(tmp/1000);
    diff.sec = tmp % 60;
  
    tmp = Math.floor((tmp-diff.sec)/60);
    diff.min = tmp % 60;
  
    tmp = Math.floor((tmp-diff.min)/60);
    diff.hour = tmp;

    // convert values to string before appying lpad below
    for (let key of Object.keys(diff)) {
      diff[key] = diff[key].toString()
    }
    
    const elapsedTimeStr = [diff.hour.padStart(4, '0'), diff.min.padStart(2, '0'), diff.sec.padStart(2, '0')].join(':')

    elt.innerHTML = elapsedTimeStr
  }