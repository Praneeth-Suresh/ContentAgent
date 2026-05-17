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

const defaultStages = [
  { name: "Market Research", summary: "Audience, channel, and competitive signals.", status: "pending" },
  { name: "Campaign Orchestration", summary: "Campaign sequence, offer, and required materials.", status: "pending" },
  { name: "Content Generation", summary: "Text, image, and video briefs ready for editing.", status: "pending" },
];

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
  const visibleStages = stages.length ? stages : defaultStages;
  stageStrip.innerHTML = "";
  visibleStages.forEach((stage) => {
    const item = document.createElement("article");
    item.className = "stage-item";
    item.dataset.status = stage.status;
    const title = document.createElement("strong");
    title.textContent = stage.name;
    const summary = document.createElement("span");
    summary.textContent = stage.summary;
    item.append(title, summary);
    stageStrip.appendChild(item);
  });
  drawWorkflowMap(visibleStages);
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
  context.fillStyle = "#120706";
  context.fillRect(0, 0, width, height);

  context.strokeStyle = "rgba(255, 244, 200, 0.08)";
  context.lineWidth = 1;
  for (let x = 0; x <= width; x += 46) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, height);
    context.stroke();
  }
  for (let y = 0; y <= height; y += 26) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(width, y);
    context.stroke();
  }

  const nodes = stages.length ? stages : defaultStages;
  const gap = width / (nodes.length + 1);
  const centerY = Math.round(height * 0.48);

  context.lineWidth = 2;
  context.strokeStyle = "rgba(216, 255, 99, 0.48)";
  context.beginPath();
  context.moveTo(gap, centerY);
  context.lineTo(width - gap, centerY);
  context.stroke();

  nodes.forEach((stage, index) => {
    const x = gap * (index + 1);
    const complete = stage.status === "complete";
    const nodeWidth = 138;
    const nodeHeight = 62;
    const y = centerY - nodeHeight / 2;
    context.fillStyle = complete ? "rgba(216, 255, 99, 0.16)" : "rgba(255, 244, 200, 0.06)";
    context.strokeStyle = complete ? "#d8ff63" : "rgba(255, 244, 200, 0.48)";
    context.lineWidth = 1.5;
    context.beginPath();
    context.rect(x - nodeWidth / 2, y, nodeWidth, nodeHeight);
    context.fill();
    context.stroke();

    context.fillStyle = complete ? "#d8ff63" : "#7dd7ff";
    context.fillRect(x - nodeWidth / 2 + 11, y + 12, 8, 8);
    context.fillStyle = "#fff4c8";
    context.font = "700 13px monospace";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(`0${index + 1}`, x, y + 22);
    context.fillStyle = "rgba(255, 244, 200, 0.72)";
    context.font = "700 12px monospace";
    context.fillText(stage.name.toUpperCase(), x, y + 43);
  });

  context.fillStyle = "rgba(255, 244, 200, 0.74)";
  context.font = "700 12px monospace";
  context.textAlign = "left";
  context.fillText("AGENT WORKFLOW MAP", 24, 30);
  context.fillStyle = "rgba(216, 255, 99, 0.78)";
  context.fillText("SIGNAL: MONETIZATION", 24, height - 26);
  context.fillStyle = "rgba(125, 215, 255, 0.72)";
  context.textAlign = "right";
  context.fillText("USER FEEDBACK LOOP ENABLED", width - 24, height - 26);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  generatePlan();
});

regenerateButton.addEventListener("click", generatePlan);
addFeedbackButton.addEventListener("click", addFeedback);
renderStages();
