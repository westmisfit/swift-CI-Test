#encoding:utf-8
import sys
import os
import requests
import argparse
import time
from jira import JIRA
import traceback
import re
import json

JIRA_SERVER = {"server":"https://misfit.jira.com"}
JIRA_AUTH = ("kentz", "1qaz2wsx")

ROOM = "TestRoom"
HIPCHAT_TOKEN = "7i7HLfO5Wlr2r1ctlm8owTO3ZeIXwxiUTN3sTc7i"

def send_hipchat_msg(msg):
	hipchat_url = "https://api.hipchat.com/v2/room/{0}/notification?auth_token={1}".format(ROOM, HIPCHAT_TOKEN)
	msg = "Travis Integrate to JIRA Error occurs! \n" + msg
	data = json.dumps({"message_format":"text", "message": msg})
	return "curl -H \"Content-Type: application/json\" -X POST -d '{0}' {1}".format(data, hipchat_url)


def load_args():
	parser = argparse.ArgumentParser()
	# parser.add_argument("-u", "--username") # username or the organization name
	# parser.add_argument("-r", "--reponame") # repo name
	parser.add_argument("-s", "--slug")
	parser.add_argument("-c", "--commitid")
	parser.add_argument("-m", "--method")
	parser.add_argument("-a", "--action") # method=change_status, then you need to input the status you want to change to.
	return parser.parse_args()

def parse_cmt(cmt):
	# -----------------------
	# COMMIT_MESSAGE contains:
	# [issue_id=MNP-40][rtype=none][issue_type=trival]update commit msg
	# -----------------------
	print "The Commit Commnet are: \n{0}".format(cmt)	
	reg_issue = r'\[issue_id\=(?P<issue>.+)\]\[rtype'
	reg_rtype = r'.*issue_id.*\]\[rtype\=(?P<rtype>.+)\]\['
	reg_issue_type = r'.*rtype.*\]\[issue_type\=(?P<issue_type>.+)\]'
	reg_msg = r'\[.+\]\[.+\](?P<msg>.+)'

	match_issue = re.match(reg_issue, cmt)
	issue_id = match_issue.group('issue').strip()

	match_rtype = re.match(reg_rtype, cmt)
	if match_rtype:
		rtype = match_rtype.group('rtype').strip()
	else:
		rtype = "none"

	match_issue_type = re.match(reg_issue_type, cmt)
	if match_issue_type:
		issue_type = match_issue_type.group('issue_type').strip()
	else:
		issue_type = "trival"

	match_msg = re.match(reg_msg, cmt)
	msg = match_msg.group('msg').strip()

	return issue_id, rtype, issue_type, msg


def change_status(issue_id, action):
	# Trigger the issue to performe the Action in order to change the status
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	transitions = jira.transitions(issue)
	t_dict = {t['name']:t['id'] for t in transitions} 
	print "Optional Action: {0}".format(t_dict)
	print "Change the Issue: {0} status. Action: {1}".format(issue_id, action)
	jira.transition_issue(issue, t_dict[action])


def current_issue_status(issue_id):
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	status = str(issue.fields.status)
	print "Current Status of the JIRA Issue is : {0}".format(status)
	return status


def test_status(testResult):
	if testResult is None:
		testStatus = TestResult.NT
	else:
		if testResult:
			testStatus = TestResult.Pass
		else:
			testStatus = TestResult.Fail
	return testStatus


# **********************************************
# Specified Test
# **********************************************
def bdd_test(issue_id):
	# CI Test Result
	#text: customfield_12103
	#radio: customfield_12007
	testResult = True
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	
	# -----------------------------------
	# Begin the BDD test
	# -----------------------------------

	# After Testing, Set the value to the JIRA
	#issue.update(customfield_12103="http://ci.misfit.com/{0}".format(time.time()))
	issue.update(customfield_12103="No Test Report Now")
	issue.update(customfield_12007={"value":test_status(testResult)})
	return testResult


def ui_check(issue_id):
	# Only Add the test result url to the field
	# UI Check Status
	#text: customfield_12105
	#radio: customfield_12009
	testResult = True
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)

	# -----------------------------------
	# Begin the ui check test
	# -----------------------------------

	# After Testing, Set the value to the JIRA
	#issue.update(customfield_12105="http://uicheck.misfit.com/{0}".format(time.time()))
	issue.update(customfield_12105="No Test Report Now")
	issue.update(customfield_12009={"value":test_status(testResult)})
	return testResult


def coverage_stat(issue_id):
	# -----------------------------------
	# Get the Coverage from Coveralls
	# -----------------------------------
	return True


def unit_test(issue_id):
	# -----------------------------------
	# Begin the unit test
	# -----------------------------------
	return True


def device_test(issue_id):
	# DT Result Status
	#text: customfield_12104
	#radio: customfield_12008
	testResult = True
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)

	# -----------------------------------
	# Begin the device test
	# -----------------------------------

	# After Testing, Set the value to the JIRA
	#issue.update(customfield_12104="http://dt.misfit.com/{0}".format(time.time()))
	issue.update(customfield_12104="No Test Report Now")
	issue.update(customfield_12008={"value":test_status(testResult)})
	return testResult


def reset(issue_id):
	# It's better to reset the test status and test report after building
	pass

# **********************************************
# Workflow Actions
# **********************************************
def implement():
	pass


def submit_code(issue_id):
	# In Progress => Code Submitted
	change_status(issue_id, IssueAction.submit_code)
	# CI Test
	ci_test_result = bdd_test(issue_id) and ui_check(issue_id) and unit_test(issue_id) and device_test(issue_id)
	if not ci_test_result:
		# CI Test Fail
		bdd_test_fail(issue_id)
	else:
		# CI Test Pass
		bdd_test_pass(issue_id)


def re_implement(issue_id):
	# CI Failed => In Progress
	change_status(issue_id, IssueAction.re_implement)
	# submit code
	submit_code(issue_id)


# BDD Test Fail == CI Test Fail
def bdd_test_fail(issue_id):
	# Code Submitted => CI Test Fail
	change_status(issue_id, IssueAction.bdd_test_fail)


# BDD Test Pass == CI Test Pass
def bdd_test_pass(issue_id):
	# Code Submitted => CI Passed
	change_status(issue_id, IssueAction.bdd_test_pass)



def continue_develop_story(issue_id):
	# CI Passed => In Progress
	change_status(issue_id, IssueAction.continue_dev)
	# continue develop story equals to the code submit
	submit_code(issue_id)


def submit_code_review(issue_id):
	# CI Passed =》 SCR Requested
	change_status(issue_id, IssueAction.submit_code_review)


def scr_check_fail():
	pass


def scr_check_pass():
	pass


def merge_story(issue_id):
	# SCR Passed => Story Merged
	change_status(issue_id, IssueAction.merge_story)
	# Auto Test
	auto_test_result = bdd_test(issue_id) and ui_check(issue_id) and unit_test(issue_id) and device_test(issue_id)
	if not auto_test_result:
		auto_test_fail(issue_id)
	else:
		auto_test_pass(issue_id)


def auto_test_fail(issue_id):
	# Story Merged => Auto Test Fail
	change_status(issue_id, IssueAction.auto_test_fail)


def auto_test_pass(issue_id):
	# Story Merged => CI Passed
	change_status(issue_id, IssueAction.auto_test_pass)


def fix_issue(issue_id):
	# SCR Fail => SCR Requested
	# Auto Test Fail => SCR Requested
	# Smoke Test Fail => SCR Requested
	change_status(issue_id, IssueAction.fix_issue)


def fix_small_issue(issue_id):
	# Auto Test Fail => Story Merged
	# Smoke Test Fail => Story Merged
	change_status(issue_id, IssueAction.fix_small_issue)
	# Trigger the auto test again
	auto_test_result = bdd_test(issue_id) and ui_check(issue_id) and unit_test(issue_id) and device_test(issue_id)
	if not auto_test_result:
		auto_test_fail(issue_id)
	else:
		auto_test_pass(issue_id)


def smoke_test_fail():
	pass


def smoke_test_pass():
	pass


# Enumeration of the Issue Action
class IssueAction:
	implement = "implement" 
	submit_code = "Submit Code" # submit code
	#---------
	bdd_test_fail = "BDD Test  Fail" # auto check
	bdd_test_pass = "BDD Test Pass" # manual check
	re_implement = "Re-implement" # submit code
	#--------
	continue_dev = "Continue Develop Story " # submit code
	submit_code_review = "Submit Code Review" 
	scr_check_fail = "SCR Check Fail" # manual check
	scr_check_pass = "SCR Check Pass" # manual check
	fix_issue = "Fix Issue"  # submit code
	merge_story = "Merge Story"
	auto_test_pass = "Auto Test Pass" # manual check
	auto_test_fail = "Auto Test Fail" # manual check
	fix_small_issue = "Fix Small Issue" # submit code
	smoke_test_fail = "Smoke Test Fail" # manual check
	smoke_test_pass = "Smoke Test Pass" # manual check



# Enumeration of the Issue Status
class IssueStatus:
	ToDo = "To Do"
	InProgress = "In Progress"
	CodeSubmitted = "Code Submitted"
	CiPassed = "CI Passed"
	CiFailed = "CI Failed"
	ScrRequested = "SCR Requested"
	#-------------
	ScrPassed = "SCR PASSED"
	ScrFailed = "SCR Failed"
	ScrMerged = "Story Merged"
	AutoTestPassed = "Auto Test Passed"
	AutoTestFailed = "Auto Test Failed"
	SmokeTestPassed = "Smoke Test Passed"
	#--------------
	SmokeTestFailed = "SMOKE TEST FAILED"
	Closed = "Closed"


# Result of the Testing
class TestResult:
	Pass = "Passed"
	Fail = "Failed"
	NT = "Not Tested"


if __name__ == "__main__":
	args = load_args()
	GIT_COMMIT_URL = "https://api.github.com/repos/{0}/{1}/git/commits/{2}".format(args.slug.split("/")[0], 
																				   args.slug.split("/")[1], 
																				   args.commitid)
	try:
		# Get the commit message from the Github api
		commit_message = requests.get(GIT_COMMIT_URL).json()["message"]

		# This commit_message is just for Testing without the Travis
		#commit_message = "[issue_id=MNP-40][rtype=none][issue_type=trival]update commit msg"
		issue_id, rtype, issue_type, msg = parse_cmt(commit_message)

		# if the current status is TODO, then change to In Progress
		if current_issue_status(issue_id) == IssueStatus.ToDo:
		 	print "Let's start our story!!"
		 	change_status(issue_id, IssueAction.implement)

		# # # Change the status of the JIRA issue
		if args.method is not None:
			if args.method == "change_status":
				change_status(issue_id, args.action)
			elif args.method == "reset":
				pass
		else:
			status = current_issue_status(issue_id)
		 	# In Progress
		 	if status == IssueStatus.InProgress:
		 		submit_code(issue_id)
		 	# CI Test Fail
		 	elif status == IssueStatus.CiFailed:
		 		re_implement(issue_id)
		 	# CI Test Pass
		 	elif status == IssueStatus.CiPassed:
		 		if rtype.lower() == "none":
		 			continue_develop_story(issue_id)
		 		else:
		 			submit_code_review(issue_id)
		 	# SCR Failed
		 	elif status == IssueStatus.ScrFailed:
		 		fix_issue(issue_id)
		 	elif status == IssueStatus.ScrPassed:
		 		merge_story(issue_id)
		 	elif status == IssueStatus.AutoTestFailed:
		 		# Big Issue
		 		if issue_type.lower() == "serious":
		 			fix_issue(issue_id)
		 		# normal issue
		 		else:
		 			fix_small_issue(issue_id)
		 	elif status == IssueStatus.SmokeTestFailed:
		 		# Big Issue
		 		if issue_type.lower() == "serious":
		 			fix_issue(issue_id)
		 		else:
		 			fix_small_issue(issue_id)
	except Exception,e:
	 	os.system(send_hipchat_msg(traceback.format_exc()))


