const form = document.querySelector("#source-form");
const sourceInput = document.querySelector("#software-source");
const generateButton = document.querySelector("#generate-button");
const regenerateButton = document.querySelector("#regenerate-button");
const feedbackStage = document.querySelector("#stage-select");
const feedbackInput = document.querySelector("#feedback-input");
const addFeedbackButton = document.querySelector("#add-feedback-button");
const feedbackList = document.querySelector("#feedback-list");
const stageStrip = document.querySelector("#stage-strip");
const statusLine = document.querySelector("#status-line");
const metrics = document.querySelector("#plan-metrics");
const planEditor = document.querySelector("#plan-editor");
const workflowMap = document.querySelector("#workflow-map");

const userInterventions = [];
let lastSource = "";

function setBusy(isBusy) {
  generateButton.disabled = isBusy;
  regenerateButton.disabled = isBusy;
  generateButton.textContent = isBusy ? "Generating" : "Generate";
}

function renderFeedback() {
  feedbackList.innerHTML = "";
  userInterventions.forEach((item) => {
    const row = document.createElement("li");
    row.textContent = `${item.stage_name}: ${item.feedback}`;
    feedbackList.appendChild(row);
  });
}

function renderStages(stages = []) {
  stageStrip.innerHTML = "";
  stages.forEach((stage) => {
    const item = document.createElement("article");
    item.className = "stage-item";
    const title = document.createElement("strong");
    title.textContent = stage.name;
    const summary = document.createElement("span");
    summary.textContent = stage.summary;
    item.append(title, summary);
    stageStrip.appendChild(item);
  });
  drawWorkflowMap(stages);
}

function renderMetrics(plan) {
  const groups = [
    ["Product", plan.software_source.product_name],
    ["Source kind", plan.software_source.kind.replace("_", " ")],
    ["Audience segments", plan.market_research.audience_segments.length],
    ["Campaign materials", plan.campaign_orchestration.required_materials.length],
    [
      "Generated content",
      `${plan.content_generation.text_assets.length} text, ${plan.content_generation.image_briefs.length} image, ${plan.content_generation.video_briefs.length} video`
    ],
  ];

  metrics.innerHTML = "";
  groups.forEach(([label, value]) => {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = label;
    detail.textContent = value;
    wrapper.append(term, detail);
    metrics.appendChild(wrapper);
  });
}

function renderPlan(plan) {
  statusLine.classList.remove("error");
  statusLine.textContent = plan.executive_summary;
  planEditor.value = plan.editable_markdown;
  renderStages(plan.generation_stages);
  renderMetrics(plan);
}

function renderError(message) {
  statusLine.classList.add("error");
  statusLine.textContent = message;
}

async function generatePlan() {
  const softwareSource = sourceInput.value.trim();
  if (!softwareSource) {
    renderError("Software Source is required.");
    return;
  }

  lastSource = softwareSource;
  setBusy(true);
  renderError("Generating Marketing Plan...");
  statusLine.classList.remove("error");

  try {
    const response = await fetch("/api/marketing-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        software_source: softwareSource,
        user_interventions: userInterventions,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to generate Marketing Plan.");
    }
    renderPlan(payload.marketing_plan);
  } catch (error) {
    renderError(error.message);
  } finally {
    setBusy(false);
  }
}

function addFeedback() {
  const feedback = feedbackInput.value.trim();
  if (!feedback) {
    renderError("Feedback is empty.");
    return;
  }
  userInterventions.push({
    stage_name: feedbackStage.value,
    feedback,
  });
  feedbackInput.value = "";
  renderFeedback();
  if (lastSource) {
    generatePlan();
  }
}

function drawWorkflowMap(stages = []) {
  const context = workflowMap.getContext("2d");
  const width = workflowMap.width;
  const height = workflowMap.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#edf5f4";
  context.fillRect(0, 0, width, height);

  const nodes = stages.length ? stages : [
    { name: "Market Research", status: "pending" },
    { name: "Campaign Orchestration", status: "pending" },
    { name: "Content Generation", status: "pending" },
  ];
  const gap = width / (nodes.length + 1);

  context.lineWidth = 5;
  context.strokeStyle = "#87aaa5";
  context.beginPath();
  context.moveTo(gap, height / 2);
  context.lineTo(width - gap, height / 2);
  context.stroke();

  nodes.forEach((stage, index) => {
    const x = gap * (index + 1);
    const complete = stage.status === "complete";
    context.beginPath();
    context.fillStyle = complete ? "#0f766e" : "#ffffff";
    context.strokeStyle = complete ? "#0f766e" : "#87aaa5";
    context.arc(x, height / 2, 26, 0, Math.PI * 2);
    context.fill();
    context.stroke();
    context.fillStyle = complete ? "#ffffff" : "#17202a";
    context.font = "700 17px system-ui";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(String(index + 1), x, height / 2);
    context.fillStyle = "#17202a";
    context.font = "700 14px system-ui";
    context.fillText(stage.name, x, height / 2 + 48);
  });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  generatePlan();
});

regenerateButton.addEventListener("click", generatePlan);
addFeedbackButton.addEventListener("click", addFeedback);
drawWorkflowMap();
