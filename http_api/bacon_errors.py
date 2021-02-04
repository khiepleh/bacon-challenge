# Errors
unknown_error = {
      'Error'       : 'Unknown Error'
    , 'Code'        : -1
    , 'Description' : 'Something unexpected happened; please try again'
}

missing_params = {
      'Error'       : 'Missing Parameters'
    , 'Code'        : -2
    , 'Description' : 'The request was missing one or more required parameters'
}

invalid_json = {
      'Error'       : 'JSON decode error'
    , 'Code'        : -3
    , 'Description' : 'There was an error attempting to decode the provided JSON'
}

multi_failed = {
      'Error'       : 'Not all degrees found'
    , 'Code'        : -4
    , 'Description' : 'At least one of the provided actor pairs could not be queried successfully'
}
