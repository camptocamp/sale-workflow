This module adds security group "Can Confirm Sales" to allow only users in it to confirm a sale order:

1. button "Confirm" in sale views is always hidden for users not in that group
2. if users outside the group try to confirm a SO, an error is raised
