#encoding:utf-8
import sys
import requests
import argparse
from jira import JIRA

JIRA_SERVER = {"server":"https://misfit.jira.com"}
JIRA_AUTH = ("kentz", "1qaz2wsx")

def load_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--username", type=str, default="kentzzhang")
	parser.add_argument("-r", "--reponame", type=str, default="swift-CI-Test")
	parser.add_argument("-c", "--commitid", type=str)
	parser.add_argument("-m", "--method")
	parser.add_argument("-s", "--action") # method=change_status, then you need to input the status you want to change to.
	return parser.parse_args()


def change_status(issue_id, action):
	print "Change the Issue: {0} status. Action: {1}".format(issue_id, action)
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	transitions = jira.transitions(issue)
	t_dict = {t['name']:t['id'] for t in transitions} 
	print "Optional Action: {0}".format(t_dict)
	jira.transition_issue(issue, t_dict[action])


def parse_cmt(cmt):
	# COMMIT_MESSAGE contains:
	# 1.issueid=****
	# 2.rtype=CR, values: CR(default value), SCR
	# 3.msg=****
	# -----------------------
	# issue_id=TP-5
	# msg=testcomment is fine. Let's go
	# -----------------------
	print "The Commit Commnet are: \n{0}".format(cmt)
	lines = cmt.split("\n")
	issue_id = lines[0][lines[0].index("=")+1:]
	rtype = lines[1][lines[1].index("=")+1:]
	msg = lines[2][lines[2].index("=")+1:]
	return issue_id, rtype, msg


def get_current_issue_status(issue_id):
	# jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	# issue = jira.issue(issue_id)
	# # ISSUE STATUS
	# print issue.id
	# print issue.key
	# print issue.fields.status
	# print issue.fields.progress
	# jira.add_comment(issue_id, "CUSTOM COMMENT !!!!")
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	status = str(issue.fields.status)
	print "Current Status of the JIRA Issue is {0}".format(status)
	return status


# **********************************************
# Specified Test
# **********************************************
def bdd_test():
	return True


def ui_check():
	# Only Add the test result url to the field
	return True


def coverage_stat():
	return True


def unit_test():
	# 
	return True


def device_test():
	# 
	return False


# **********************************************
# Workflow Actions
# **********************************************
def commit_cr(issue_id):
	# In Progress => CR Test Completed
	change_status(issue_id, IssueAction.CommitCr)
	# Begin to test after committing
	crTestResult = bdd_test() and unit_test() and device_test()
	if not crTestResult:
		# if there is any fail result, go to the issue fixing status
		fix_cr_issue(issue_id)
	# else branch need to change the status manually


def commit_scr(issue_id):
	# In Progress => SCR Test Completed
	change_status(issue_id, IssueAction.CommitScr)
	# Begin to test after committing
	scrTestResult = bdd_test() and unit_test() and device_test()
	if not scrTestResult:
		# if there is any fail result, go to the in progress status
		fail_scr_test(issue_id)
	# else branch need to change the status manually


def start_smoke_test(issue_id):
	# SCR Test Completed => Smoke Testing
	change_status(issue_id, IssueAction.StartSmokeTest)


def commit_smoke(issue_id):
	# Smoke Testing => In Progress
	change_status(issue_id, IssueAction.CommitSmoke)


def fail_scr_test(issue_id):
	# SCR Test Completed => In Progress
	change_status(issue_id, IssueAction.FailScrTest)


def fix_cr_issue(issue_id):
	# CR Test Completed => CR Fixing
	change_status(issue_id, IssueAction.FixCrIssue)


def commit_issue(issue_id):
	# CR Fixing => CR Test Completed
	change_status(issue_id, IssueAction.CommitIssue)
	# Begin to test after committing
	crTestResult = bdd_test() and unit_test() and device_test()
	if not crTestResult:
		# if there is any fail result, go to the issue fixing status
		fix_cr_issue(issue_id)
	# else branch need to change the status manually


def pass_cr_test(issue_id):
	# CR Test Completed => In Progress
	change_status(issue_id, IssueAction.PassCrTest)


# Enum of the Issue Action
class IssueAction:
	StartStory = "Start Story"
	CommitScr = "Commit SCR"
	CommitCr = "Commit CR"
	FailScrTest = "Fail SCR Test"
	PassCrTest = "Pass CR Test"
	FixCrIssue = "Fix CR Issue"
	CommitIssue = "Commit Issue"
	StartSmokeTest = "Start Smoke Test"
	CommitSmoke = "Commit Smoke"
	PassSmokeTest = "Pass Smoke Test"


# Enum of the Issue Status
class IssueStatus:
	ToDo = "ToDo"
	InProgress = "In Progress"
	CrTestCompleted = "CR Test Completed"
	ScrTestCompleted = "SCR Test Completed"
	CrFixing = "CR Fixing"
	SmokeTesting = "Smoke Testing"
	Done = "Done"


if __name__ == "__main__":
	args = load_args()
	GIT_COMMIT_URL = "https://api.github.com/repos/{0}/{1}/git/commits/{2}".format(args.username, 
																				   args.reponame, 
																				   args.commitid)
	commit_message = requests.get(GIT_COMMIT_URL).json()["message"]
	#commit_message = "issueid=TP-10\nrtype=SCR\nmsg=update commit"
	issue_id, rtype, msg = parse_cmt(commit_message)

	# if the current status is TODO, then change to In Progress
	if get_current_issue_status(issue_id) == IssueStatus.ToDo:
		print "Let's start our story!!"
		change_status(issue_id, IssueAction.StartStory)

	# Change the status of the JIRA issue
	if args.method is not None:
		if args.method == "change_status":
			change_status(issue_id, args.action)
	else:
		# In Progress
		if get_current_issue_status(issue_id) == IssueStatus.InProgress:
			# SCR Commit
			if rtype.upper() == "SCR":
				commit_scr(issue_id)

			# CR Commit
			elif rtype.upper() == "CR":
				commit_cr(issue_id)

		# CR Test Completed
		# *********************************************************************************************
		# ****** We need to change the status "CrTestCompleted" manually without fail test result******
		# *********************************************************************************************
		# elif get_current_issue_status(issue_id) == IssueStatus.CrTestCompleted:
		# 	crTestResult = bdd_test() and unit_test() and device_test()
		# 	# Test Pass
		# 	if crTestResult:
		# 		pass_cr_test(issue_id)
		# 	# Test Fail
		# 	else:
		# 		fix_cr_issue(issue_id)


		# CR Fixing
		elif get_current_issue_status(issue_id) == IssueStatus.CrFixing:
			commit_issue(issue_id


		# SCR Test Completed
		# *********************************************************************************************
		# ****** We need to change the status "ScrTestCompleted" manually without fail test result******
		# *********************************************************************************************
		# elif get_current_issue_status(issue_id) == IssueStatus.ScrTestCompleted:
		# 	scrTestResult = bdd_test() and unit_test() and device_test()
		# 	# Test Fail
		# 	if not scrTestResult:
		# 		fail_scr_test(issue_id)