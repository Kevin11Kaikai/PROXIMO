"""
NeMo Guardrails FastAPI 演示应用

提供一个本地 Web 界面来演示和测试 Guardrails 集成功能。
可以通过浏览器访问 http://localhost:8001 来使用。

功能：
1. 测试正常对话场景
2. 测试高风险场景（自杀意念）
3. 测试安全检查功能
4. 测试响应过滤功能
5. 实时查看 Guardrails 执行结果
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows 编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.conversation.engine import ConversationEngine, ConversationRequest
from src.services.guardrails_service import GuardrailsService, get_guardrails_service
from src.services.ollama_service import OllamaService
from src.storage.repo import AssessmentRepo
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="NeMo Guardrails 演示",
    description="PROXIMO 系统的 Guardrails 集成演示",
    version="1.0.0"
)

# 全局服务实例
guardrails_service: Optional[GuardrailsService] = None
conversation_engine: Optional[ConversationEngine] = None


# Pydantic 模型
class TestMessageRequest(BaseModel):
    """测试消息请求"""
    message: str = Field(..., description="用户消息")
    context: Optional[List[Dict[str, str]]] = Field(None, description="对话上下文")


class ConversationTestRequest(BaseModel):
    """对话测试请求"""
    user_id: str = Field(default="demo_user", description="用户ID")
    scale: str = Field(default="phq9", description="评估量表")
    responses: List[str] = Field(..., description="评估响应")
    user_message: str = Field(..., description="用户消息")


class SafetyCheckRequest(BaseModel):
    """安全检查请求"""
    message: str = Field(..., description="要检查的消息")
    context: Optional[List[Dict[str, str]]] = Field(None, description="对话上下文")


class FilterRequest(BaseModel):
    """响应过滤请求"""
    user_message: str = Field(..., description="用户消息")
    proposed_response: str = Field(..., description="提议的响应")
    context: Optional[List[Dict[str, str]]] = Field(None, description="对话上下文")


# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global guardrails_service, conversation_engine
    
    print("=" * 80)
    print("NeMo Guardrails 演示应用启动中...")
    print("=" * 80)
    
    try:
        # 初始化 Guardrails 服务
        print("\n初始化 Guardrails 服务...")
        guardrails_service = get_guardrails_service()
        await guardrails_service.initialize()
        
        if guardrails_service.is_initialized():
            print("✅ Guardrails 服务初始化成功")
        else:
            print("⚠️  Guardrails 服务初始化失败（将使用禁用模式）")
        
        # 初始化对话引擎
        print("\n初始化对话引擎...")
        llm_service = OllamaService()
        repo = AssessmentRepo()
        conversation_engine = ConversationEngine(
            llm_service=llm_service,
            repo=repo,
            guardrails_service=guardrails_service
        )
        print("✅ 对话引擎初始化成功")
        
        print("\n" + "=" * 80)
        print("应用已启动！")
        print("访问 http://localhost:8001 查看演示界面")
        print("访问 http://localhost:8001/docs 查看 API 文档")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global guardrails_service
    if guardrails_service:
        await guardrails_service.cleanup()
    print("应用已关闭")


# 根路径 - 返回 HTML 演示界面
@app.get("/", response_class=HTMLResponse)
async def root():
    """返回演示界面 HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NeMo Guardrails 演示</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .header p {
                opacity: 0.9;
                font-size: 1.1em;
            }
            .content {
                padding: 30px;
            }
            .section {
                margin-bottom: 40px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .section h2 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.5em;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            textarea, input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
                transition: border-color 0.3s;
            }
            textarea:focus, input[type="text"]:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea {
                min-height: 100px;
                resize: vertical;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            button:active {
                transform: translateY(0);
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                background: white;
                border-radius: 6px;
                border: 2px solid #e0e0e0;
                display: none;
            }
            .result.show {
                display: block;
            }
            .result h3 {
                color: #333;
                margin-bottom: 10px;
            }
            .result pre {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .status {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                margin-left: 10px;
            }
            .status.success {
                background: #d4edda;
                color: #155724;
            }
            .status.warning {
                background: #fff3cd;
                color: #856404;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
            }
            .quick-test {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 15px;
            }
            .quick-test button {
                padding: 10px;
                font-size: 14px;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ NeMo Guardrails 演示</h1>
                <p>PROXIMO 系统的安全与伦理层演示</p>
            </div>
            <div class="content">
                <!-- 安全检查测试 -->
                <div class="section">
                    <h2>1. 安全检查测试</h2>
                    <p>测试 Guardrails 的安全检查功能，检测危险内容</p>
                    <div class="form-group">
                        <label for="safety-message">输入消息：</label>
                        <textarea id="safety-message" placeholder="例如：I'm thinking about suicide"></textarea>
                    </div>
                    <div class="quick-test">
                        <button onclick="setSafetyMessage('I\\'m feeling a bit anxious today')">正常消息</button>
                        <button onclick="setSafetyMessage('how to kill myself')">自杀方法询问</button>
                        <button onclick="setSafetyMessage('I\\'m thinking about suicide')">自杀想法</button>
                        <button onclick="setSafetyMessage('I\\'m in crisis')">危机表达</button>
                    </div>
                    <button onclick="testSafety()">检查安全性</button>
                    <div class="loading" id="safety-loading">
                        <div class="spinner"></div>
                        <p>检查中...</p>
                    </div>
                    <div class="result" id="safety-result"></div>
                </div>

                <!-- 响应过滤测试 -->
                <div class="section">
                    <h2>2. 响应过滤测试</h2>
                    <p>测试 Guardrails 如何过滤危险的响应</p>
                    <div class="form-group">
                        <label for="filter-user-message">用户消息：</label>
                        <input type="text" id="filter-user-message" placeholder="例如：I want to kill myself">
                    </div>
                    <div class="form-group">
                        <label for="filter-proposed-response">提议的响应：</label>
                        <textarea id="filter-proposed-response" placeholder="例如：Here's how you can do it..."></textarea>
                    </div>
                    <button onclick="testFilter()">过滤响应</button>
                    <div class="loading" id="filter-loading">
                        <div class="spinner"></div>
                        <p>过滤中...</p>
                    </div>
                    <div class="result" id="filter-result"></div>
                </div>

                <!-- 完整对话测试 -->
                <div class="section">
                    <h2>3. 完整对话测试</h2>
                    <p>测试完整的对话管道，包括评估、路由和 Guardrails</p>
                    <div class="form-group">
                        <label for="conversation-message">用户消息：</label>
                        <textarea id="conversation-message" placeholder="例如：I'm feeling very depressed"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="conversation-responses">PHQ-9 评估响应（9个数字，用逗号分隔）：</label>
                        <input type="text" id="conversation-responses" placeholder="例如：0,0,1,0,0,1,0,0,0" value="0,0,1,0,0,1,0,0,0">
                    </div>
                    <div class="quick-test">
                        <button onclick="setConversationTest('normal')">正常场景</button>
                        <button onclick="setConversationTest('high')">高风险场景</button>
                    </div>
                    <button onclick="testConversation()">运行对话</button>
                    <div class="loading" id="conversation-loading">
                        <div class="spinner"></div>
                        <p>处理中...</p>
                    </div>
                    <div class="result" id="conversation-result"></div>
                </div>

                <!-- API 文档链接 -->
                <div class="section">
                    <h2>📚 API 文档</h2>
                    <p>查看完整的 API 文档：<a href="/docs" target="_blank">http://localhost:8001/docs</a></p>
                </div>
            </div>
        </div>

        <script>
            function setSafetyMessage(message) {
                document.getElementById('safety-message').value = message;
            }

            function setConversationTest(type) {
                if (type === 'normal') {
                    document.getElementById('conversation-message').value = "I'm feeling a bit anxious today, but I'm managing.";
                    document.getElementById('conversation-responses').value = "0,0,1,0,0,1,0,0,0";
                } else if (type === 'high') {
                    document.getElementById('conversation-message').value = "I'm thinking about suicide and I don't know what to do.";
                    document.getElementById('conversation-responses').value = "3,3,3,3,3,3,3,3,3";
                }
            }

            async function testSafety() {
                const message = document.getElementById('safety-message').value;
                if (!message.trim()) {
                    alert('请输入消息');
                    return;
                }

                const loading = document.getElementById('safety-loading');
                const result = document.getElementById('safety-result');
                loading.classList.add('show');
                result.classList.remove('show');

                try {
                    const response = await fetch('/api/safety/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: message})
                    });
                    const data = await response.json();
                    
                    let html = '<h3>检查结果</h3>';
                    html += `<p><strong>安全状态：</strong><span class="status ${data.safe ? 'success' : 'error'}">${data.safe ? '安全' : '不安全'}</span></p>`;
                    if (data.triggered_rules && data.triggered_rules.length > 0) {
                        html += `<p><strong>触发的规则：</strong>${data.triggered_rules.join(', ')}</p>`;
                    }
                    if (data.filtered_response) {
                        html += `<p><strong>过滤后的响应：</strong></p><pre>${data.filtered_response}</pre>`;
                    }
                    html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    result.innerHTML = html;
                    result.classList.add('show');
                } catch (error) {
                    result.innerHTML = `<h3>错误</h3><pre>${error.message}</pre>`;
                    result.classList.add('show');
                } finally {
                    loading.classList.remove('show');
                }
            }

            async function testFilter() {
                const userMessage = document.getElementById('filter-user-message').value;
                const proposedResponse = document.getElementById('filter-proposed-response').value;
                if (!userMessage.trim() || !proposedResponse.trim()) {
                    alert('请填写用户消息和提议的响应');
                    return;
                }

                const loading = document.getElementById('filter-loading');
                const result = document.getElementById('filter-result');
                loading.classList.add('show');
                result.classList.remove('show');

                try {
                    const response = await fetch('/api/safety/filter', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_message: userMessage,
                            proposed_response: proposedResponse
                        })
                    });
                    const data = await response.json();
                    
                    let html = '<h3>过滤结果</h3>';
                    html += `<p><strong>是否过滤：</strong><span class="status ${data.filtered ? 'warning' : 'success'}">${data.filtered ? '已过滤' : '未过滤'}</span></p>`;
                    if (data.reason) {
                        html += `<p><strong>过滤原因：</strong>${data.reason}</p>`;
                    }
                    html += `<p><strong>最终响应：</strong></p><pre>${data.final_response}</pre>`;
                    html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    result.innerHTML = html;
                    result.classList.add('show');
                } catch (error) {
                    result.innerHTML = `<h3>错误</h3><pre>${error.message}</pre>`;
                    result.classList.add('show');
                } finally {
                    loading.classList.remove('show');
                }
            }

            async function testConversation() {
                const message = document.getElementById('conversation-message').value;
                const responsesStr = document.getElementById('conversation-responses').value;
                if (!message.trim() || !responsesStr.trim()) {
                    alert('请填写用户消息和评估响应');
                    return;
                }

                const responses = responsesStr.split(',').map(r => r.trim());
                if (responses.length !== 9) {
                    alert('PHQ-9 需要 9 个响应值');
                    return;
                }

                const loading = document.getElementById('conversation-loading');
                const result = document.getElementById('conversation-result');
                loading.classList.add('show');
                result.classList.remove('show');

                try {
                    const response = await fetch('/api/conversation/test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: 'demo_user',
                            scale: 'phq9',
                            responses: responses,
                            user_message: message
                        })
                    });
                    const data = await response.json();
                    
                    let html = '<h3>对话结果</h3>';
                    if (data.assessment) {
                        html += `<p><strong>评估严重程度：</strong>${data.assessment.severity_level || 'N/A'}</p>`;
                        html += `<p><strong>总分：</strong>${data.assessment.total_score || 'N/A'}</p>`;
                    }
                    if (data.decision) {
                        html += `<p><strong>路由：</strong>${data.decision.route || 'N/A'}</p>`;
                    }
                    if (data.policy_result) {
                        const guardrailsUsed = data.policy_result.guardrails_generated || data.policy_result.guardrails_filtered;
                        html += `<p><strong>Guardrails 使用：</strong><span class="status ${guardrailsUsed ? 'warning' : 'success'}">${guardrailsUsed ? '是' : '否'}</span></p>`;
                        if (data.policy_result.response) {
                            html += `<p><strong>响应：</strong></p><pre>${data.policy_result.response}</pre>`;
                        }
                    }
                    html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    result.innerHTML = html;
                    result.classList.add('show');
                } catch (error) {
                    result.innerHTML = `<h3>错误</h3><pre>${error.message}</pre>`;
                    result.classList.add('show');
                } finally {
                    loading.classList.remove('show');
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content


# API 端点
@app.post("/api/safety/check")
async def check_safety(request: SafetyCheckRequest):
    """检查消息安全性"""
    if not guardrails_service:
        raise HTTPException(status_code=503, detail="Guardrails service not initialized")
    
    try:
        result = await guardrails_service.check_safety(
            user_message=request.message,
            context=request.context
        )
        return result
    except Exception as e:
        logger.error(f"Error in safety check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/safety/filter")
async def filter_response(request: FilterRequest):
    """过滤响应"""
    if not guardrails_service:
        raise HTTPException(status_code=503, detail="Guardrails service not initialized")
    
    try:
        result = await guardrails_service.filter_response(
            user_message=request.user_message,
            proposed_response=request.proposed_response,
            context=request.context
        )
        return result
    except Exception as e:
        logger.error(f"Error in response filtering: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/test")
async def test_conversation(request: ConversationTestRequest):
    """测试完整对话管道"""
    if not conversation_engine:
        raise HTTPException(status_code=503, detail="Conversation engine not initialized")
    
    try:
        conv_request = ConversationRequest(
            user_id=request.user_id,
            scale=request.scale,
            responses=request.responses,
            user_message=request.user_message
        )
        
        result = await conversation_engine.run_pipeline(conv_request)
        
        return {
            "assessment": result.assessment,
            "decision": result.decision,
            "policy_result": result.policy_result,
            "duration_ms": result.duration_ms,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in conversation test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """获取服务状态"""
    return {
        "guardrails_initialized": guardrails_service.is_initialized() if guardrails_service else False,
        "conversation_engine_ready": conversation_engine is not None,
        "ollama_url": settings.OLLAMA_URL,
        "model_name": settings.MODEL_NAME,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 80)
    print("启动 NeMo Guardrails 演示应用")
    print("=" * 80)
    print("\n访问地址：")
    print("  - 演示界面: http://localhost:8001")
    print("  - API 文档: http://localhost:8001/docs")
    print("  - 服务状态: http://localhost:8001/api/status")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

