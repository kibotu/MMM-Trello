/* Magic Mirror
 * Node Helper: Trello
 *
 * By Joseph Bethge
 * MIT Licensed.
 */

const Trello = require("./node-trello-lite");
const NodeHelper = require("node_helper");

module.exports = NodeHelper.create({
    // Subclass start method.
    start: function() {
        var self = this;
        console.log("Starting node helper for: " + self.name);

        self.api_key = ""
        self.token = ""
        self.list = ""

        self.trelloConnections = {};
    },

    // Subclass socketNotificationReceived received.
    socketNotificationReceived: function(notification, payload) {
        var self = this;

        if (notification === "TRELLO_CONFIG") {
            self.createTrelloConnection(payload.id, payload.api_key, payload.token);
        }

        if (notification === "REQUEST_LIST_CONTENT") {
            const list = payload.list;
            const id = payload.id;

            self.retrieveListContent(list, id);
        }
    },

    // create trello connection
    createTrelloConnection: function(id, key, token) {
        var self = this;

        if (key === "")
        {
            var error = {statusCode: 400, statusMessage: "api_key is empty", responseBody: "Please add it."};
            self.sendSocketNotification("TRELLO_ERROR", {id: id, error: error});
            return;
        }

        self.trelloConnections[id] = new Trello(key, token);
    },

    // retrieve list content
    retrieveListContent: async function(list, id) {
        var self = this;

        if (!self.trelloConnections[id]) {
            return;
        }
        const trello = self.trelloConnections[id];

        try {
            const cards = await trello.getCards(list);

            if (!cards || !Array.isArray(cards)) {
                throw {
                    statusCode: 500,
                    statusMessage: "Invalid response",
                    responseBody: "Cards data is not an array"
                };
            }

            // Fetch members if not included in response
            const allMemberIds = new Set();
            cards.forEach(card => {
                if (card.idMembers && card.idMembers.length > 0) {
                    card.idMembers.forEach(memberId => allMemberIds.add(memberId));
                }
            });

            // If members are not already in the response, fetch them
            if (allMemberIds.size > 0 && (!cards[0] || !cards[0].members)) {
                try {
                    const memberPromises = Array.from(allMemberIds).map(memberId => 
                        trello.getMember(memberId).catch(err => {
                            console.log(`Failed to fetch member ${memberId}:`, err);
                            return null;
                        })
                    );
                    const members = await Promise.all(memberPromises);
                    const memberData = {};
                    members.forEach(member => {
                        if (member) {
                            memberData[member.id] = member;
                        }
                    });

                    // Attach members to cards
                    cards.forEach(card => {
                        if (card.idMembers && card.idMembers.length > 0) {
                            card.members = card.idMembers
                                .map(memberId => memberData[memberId])
                                .filter(m => m !== undefined && m !== null);
                        }
                    });
                } catch (memberError) {
                    console.log("Error fetching members, continuing without member data:", memberError);
                }
            }

            //Get all checklists before sending list
            const cardsWithChecklists = cards.filter(d => !!d.idChecklists);
            const checkListIds = cardsWithChecklists.flatMap(card => card.idChecklists);
            const checklistData = await Promise.all(checkListIds.map(id => trello.getChecklist(id)));
            for (const checklist of checklistData) {
                self.sendSocketNotification("CHECK_LIST_CONTENT", {id, data: checklist});
            }

            // Then send the list
            self.sendSocketNotification("LIST_CONTENT", {id, data: cards});
        }
        catch(error) {
            console.log(error);
            // Format error to ensure it has the expected structure
            const formattedError = {
                statusCode: error.statusCode || error.status || 500,
                statusMessage: error.statusMessage || error.message || "Unknown error",
                responseBody: error.responseBody || error.toString() || "No error details available"
            };
            self.sendSocketNotification("TRELLO_ERROR", {id, error: formattedError});
            return;
        }
    },
});
