{IMPORTS}
function handler(event){{
    var eventType = event.context.eventType;
    var functions = [{FUNCTION_LIST}];
    console.log("Event type :"+eventType);

    // we only care whether its a viewer-request as some intermediate modules may generate a response
    // at which stage we terminate the sequence and proceed with the response.
    var requestType = (eventType == "viewer-request") ? true : false;
    var length = functions.length;
    console.log(length)
    for(var i = 0;i< length; i++){{
        console.log("Executing function :"+[i]);
        var response = functions[i](event);
        if(requestType){{
            event.request = response;
        }}
        else{{
            event.response = response;
        }}

        if(shouldTerminate(response,requestType)){{
            break;
        }}
    }}

    if(requestType){{
        return event.request;
    }}
    return event.response;
}}

// determine if the function execution sequence should proceed or terminated.
// depends on the request type and if there is a statusCode present.
// Eg: if its viewer request type and there's a statusCode it implies we have a response
// and need to terminate the sequence
function shouldTerminate(functionResponse, requestType) {{
    var statusCode = functionResponse.statusCode != undefined ? true : false;
    return (requestType && statusCode) ? true : false;
}}

{FUNCTION_CODE}
