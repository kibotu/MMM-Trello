var querystring = require("querystring");

// Creates a new Trello request wrapper.
// Syntax: new Trello(applicationApiKey, userToken)
var Trello = module.exports = function (key, token) {
  if (!key) {
    throw new Error("Application API key is required");
  }

  this.key = key;
  this.token = token;
  this.host = "https://api.trello.com";
};

Trello.prototype.getCards = async function (listId) {
  const queryString = querystring.stringify(this.addAuthArgs({
    fields: "name,desc,due,idChecklists,idMembers",
    members: "all",
    member_fields: "id,avatarUrl,fullName,initials"
  }));
  const res = await fetch(`${this.host}/1/lists/${listId}/cards?${queryString}`);
  if (res.ok) {
    return res.json();
  }
}

Trello.prototype.getChecklist = async function (checkListId) {
  const queryString = querystring.stringify(this.addAuthArgs({}));
  const res = await fetch(`${this.host}/1/checklists/${checkListId}?${queryString}`);
  if (res.ok) {
    return res.json();
  }
}

Trello.prototype.addAuthArgs = function (args) {
  args.key = this.key;

  if (this.token) {
    args.token = this.token;
  }

  return args;
};

Trello.prototype.parseQuery = function (uri, args) {
  if (uri.indexOf("?") !== -1) {
    var ref = querystring.parse(uri.split("?")[1]);

    for (var key in ref) {
      var value = ref[key];
      args[key] = value;
    }
  }

  return args;
};
