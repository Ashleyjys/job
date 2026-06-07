from app.services.workflow_loader import load_workflow


def test_load_workflow_from_yaml():
    workflow = load_workflow("main")

    assert workflow.id == "main"
    assert workflow.name == "air-quality-weather-dashboard"
    assert workflow.config.forecastDays == 7
    assert workflow.config.thresholds.highRisk == 70
    assert workflow.steps[0].id == "validate_input"
