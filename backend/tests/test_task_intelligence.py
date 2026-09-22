from task_intelligence import analyze_task_requirements


def test_saved_file_requires_write_evidence():
    requirements = analyze_task_requirements("Create calculator.py in my Documents folder")
    assert requirements.requires_tools
    assert requirements.required_tool_names == {"write_file", "read_file"}


def test_current_facts_require_search_evidence():
    requirements = analyze_task_requirements("What is the latest AI news today?")
    assert requirements.required_tool_names == {"parallel_web_search"}


def test_general_question_does_not_force_tools():
    requirements = analyze_task_requirements("Explain what a Python function is")
    assert not requirements.requires_tools


def test_follow_up_run_requires_launch_of_verified_file():
    context = "Verified tool output: write_file succeeded for C:/Users/test/Documents/calculator.py"
    requirements = analyze_task_requirements("run it for me", context)
    assert requirements.required_tool_names == {"launch_app"}
