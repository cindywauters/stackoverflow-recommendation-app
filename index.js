/**
 * This is the main entrypoint to your Probot app
 * @param {import('probot').Application} app
 */
module.exports = app => {
  app.on('issues.opened', async context => {
    app.log(context)
    var issueTitle = context.payload.issue.title
    var issueLabels = ""
    for (var i in context.payload.issue.labels) {issueLabels += (context.payload.issue.labels[i].name) + ' ';}
    var issueBody = context.payload.issue.body
    var full = issueBody + " " + issueTitle

    //calling python code from https://stackoverflow.com/questions/23450534/how-to-call-a-python-function-from-node-js
    const spawn = require("child_process").spawn;
    const pythonProcess = spawn('python',["pythoncode.py", full]);

    //context.github.issues.createComment(context.issue({ body: "spawned process"}))

    pythonProcess.stderr.on('data', function(data) {
   //   context.github.issues.createComment(context.issue({ body: data.toString()}));
    });


    pythonProcess.stdout.on('data', (data) => {
      all_ids = data.toString().split("\n");
      all_ids.pop();
      var bodyComment = "The following stackoverflow posts might be useful: \n "
      for (var i = 0; i < all_ids.length; i++) {
        all_components = all_ids[i].toString().split(" ")
        bodyComment+="<a href=https://www.stackoverflow.com/questions/"
        bodyComment+=all_components[0]
        bodyComment+=">"
        for(var n = 1; n < all_components.length; n++){
        bodyComment+=all_components[n]
        bodyComment+=" "
        }
        bodyComment+="</a>\n"
      }
      const issueComment = context.issue({ body:bodyComment});// "the following SO post might help: " + data.toString()})
      return context.github.issues.createComment(issueComment)
     });
  

  })
}
