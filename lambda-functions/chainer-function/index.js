'use strict';
const global_functions_list = require("./functions.json");
const util = require('util');
const assert = require('assert');

let modules_loaded = {};
let global_function_details = {};

// initialise the modules with event type and array of functions to be executed
const init = async() => {
    let keys = Object.keys(global_functions_list);

    for (let i = 0; i < keys.length; i++) {
        let key = keys[i];

        modules_loaded[key] = {};
        global_function_details[key] = {};
        global_functions_list[key].map((functionDetails) => {
            console.log("Function details :%j",functionDetails);
            let functionName = functionDetails["function_name"];
            let functionHandler = functionDetails["handler"].split(".");
            console.log("Loading module :%s => %s.%s", functionName, functionHandler[0],functionHandler[1]);
            modules_loaded[key][functionName] = require(util.format("./lib/%s/%s.js", functionName,functionHandler[0]));
            global_function_details[key][functionName] = {"handler":functionHandler[1]};
        });
    }
};

const initialized = init();

exports.handler = async function(event, context) {

    console.log(event);
    // fetch the event type whether origin-request,origin-response, viewer-request or viewer-response
    // this is used to identify whether we need to act on the request or response part of the payload
    let eventType = event.Records[0].cf.config.eventType;

    // we check whether its a origin-request, viewer-request because in these event types
    // some of the intermediate modules may generate a response
    // at which stage we terminate the sequence and proceed with the response.
    let requestType = (eventType == "origin-request" || eventType == "viewer-request") ? true : false;

    let functions_list = null;
    let functions_handler = null;
    let function_details = null

    try {
        console.log("In handler for :%s", eventType);
        functions_list = modules_loaded[eventType];
        console.log("Functions to be executed :%s", functions_list);
        function_details = global_function_details[eventType];
        // check if functions are listed else throw an error
        assert(functions_list);
    }
    catch (error) {
        console.log("No functions defined for this side to process :%s %s", eventType,error);
        return requestType ? event.Records[0].cf.request : event.Records[0].cf.response;
    }

    let functionKeys = Object.keys(functions_list);

    // loop through the modules and evaluate
    for (var i = 0; i < functionKeys.length; i++) {
        let funcDetail = function_details[functionKeys[i]];
        let funcObj = functions_list[functionKeys[i]][funcDetail["handler"]];
        console.log("Executing Function :%s", functionKeys[i]);
        let numberOfParameters = funcObj.length;
        let functionResponse = null;
        // depending on the arguments expected by individual modules set them
        if (numberOfParameters == 1){
          console.log("Calling with 1 parameters");
            functionResponse = await funcObj(event);
        }
        else if (numberOfParameters == 2){
          console.log("Calling with 2 parameters");
            functionResponse = await funcObj(event, context);
        }
        else if (numberOfParameters == 3){
            // set a callback to catch the response coming from the module
            console.log("Calling with 3 parameters");
            await funcObj(event, context, function(){
              // console.log("Callback received :%j",arguments);
              functionResponse = arguments[1];
            });
        }
        console.log("Resp :%j",functionResponse);

          // determine if the function execution sequence should proceed or terminated.
          // depends on the request type and if there is a statusCode present.
          // Eg: if its request type and there's a statusCode it implies we have a response
          // and need to terminate the sequence
          if (shouldTerminate(functionResponse, requestType))
              return functionResponse;

          // set the processed output to the appropraite object, whether request or response
          if (requestType)
              event.Records[0].cf.request = functionResponse;
          else
              event.Records[0].cf.response = functionResponse;
    }

    console.log("Output from %j", event);
    // return the processed output depending on the requestType, whether request or response
    return requestType ? event.Records[0].cf.request : event.Records[0].cf.response;
};

function shouldTerminate(functionResponse, requestType) {
    let statusCode = functionResponse.status != undefined ? true : false;
    console.log("Request type: %s ,Status code :%s", requestType, functionResponse.status);
    return (requestType && statusCode) ? true : false;
}
