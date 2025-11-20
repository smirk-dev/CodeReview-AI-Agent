"""
Async Parallel Agent Executor
Enables parallel execution of independent agents for 2-3x performance improvement
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)

class ParallelAgentExecutor:
    """Executes agents in parallel where possible"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_agent_async(
        self,
        agent_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Run a single agent asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self.executor,
                functools.partial(agent_func, *args, **kwargs)
            )
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_parallel_agents(
        self,
        agent_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run multiple agents in parallel
        
        Args:
            agent_tasks: List of dicts with 'name', 'func', 'args', 'kwargs'
        
        Returns:
            Dict with results from all agents
        """
        tasks = []
        for task in agent_tasks:
            agent_name = task['name']
            agent_func = task['func']
            args = task.get('args', ())
            kwargs = task.get('kwargs', {})
            
            logger.info(f"Scheduling agent: {agent_name}")
            tasks.append(self.run_agent_async(agent_func, *args, **kwargs))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Package results
        output = {}
        for i, task in enumerate(agent_tasks):
            agent_name = task['name']
            result = results[i]
            
            if isinstance(result, Exception):
                output[agent_name] = {
                    "status": "error",
                    "error": str(result)
                }
            else:
                output[agent_name] = result
        
        return output
    
    async def run_sequential_with_context(
        self,
        agent_tasks: List[Dict[str, Any]],
        shared_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run agents sequentially when they depend on previous results
        Each agent receives context from previous agents
        """
        results = {}
        
        for task in agent_tasks:
            agent_name = task['name']
            agent_func = task['func']
            args = task.get('args', ())
            kwargs = task.get('kwargs', {})
            
            # Add shared context to kwargs
            kwargs['context'] = shared_context
            
            logger.info(f"Running agent sequentially: {agent_name}")
            result = await self.run_agent_async(agent_func, *args, **kwargs)
            
            results[agent_name] = result
            
            # Update shared context with this agent's results
            if result['status'] == 'success':
                shared_context[agent_name] = result['result']
        
        return results
    
    async def run_hybrid_pipeline(
        self,
        parallel_groups: List[List[Dict[str, Any]]],
        shared_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run agents in a hybrid mode:
        - Parallel within each group
        - Sequential between groups
        
        Example:
        Group 1: [CodeAnalyzer, SecurityChecker] run in parallel
        Group 2: [QualityReviewer] runs after Group 1 completes
        """
        all_results = {}
        
        for group_idx, agent_group in enumerate(parallel_groups):
            logger.info(f"Executing parallel group {group_idx + 1}/{len(parallel_groups)}")
            
            # Add context to all agents in this group
            for task in agent_group:
                task.setdefault('kwargs', {})['context'] = shared_context
            
            # Run this group in parallel
            group_results = await self.run_parallel_agents(agent_group)
            
            # Merge results
            all_results.update(group_results)
            
            # Update context with results from this group
            for agent_name, result in group_results.items():
                if result['status'] == 'success':
                    shared_context[agent_name] = result['result']
        
        return all_results
    
    def close(self):
        """Close the executor"""
        self.executor.shutdown(wait=True)

class AgentPipeline:
    """High-level agent pipeline orchestrator"""
    
    def __init__(self, execution_mode: str = "sequential"):
        """
        Args:
            execution_mode: 'sequential', 'parallel', or 'hybrid'
        """
        self.execution_mode = execution_mode
        self.executor = ParallelAgentExecutor()
    
    async def execute(
        self,
        agents: Dict[str, Callable],
        code: str,
        language: str,
        memory_bank: Any,
        tools: Any
    ) -> Dict[str, Any]:
        """
        Execute agent pipeline based on mode
        
        Args:
            agents: Dict of agent_name -> agent instance
            code: Code to review
            language: Programming language
            memory_bank: Shared memory
            tools: Analysis tools
        """
        shared_context = {
            'code': code,
            'language': language,
            'memory_bank': memory_bank,
            'tools': tools
        }
        
        if self.execution_mode == "parallel":
            return await self._execute_parallel(agents, shared_context)
        elif self.execution_mode == "hybrid":
            return await self._execute_hybrid(agents, shared_context)
        else:
            return await self._execute_sequential(agents, shared_context)
    
    async def _execute_parallel(
        self,
        agents: Dict[str, Callable],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all independent agents in parallel"""
        tasks = []
        
        # Code analyzer and security checker can run in parallel
        if 'code_analyzer' in agents:
            tasks.append({
                'name': 'code_analyzer',
                'func': agents['code_analyzer'].analyze,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        if 'security_checker' in agents:
            tasks.append({
                'name': 'security_checker',
                'func': agents['security_checker'].check,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        # Run parallel agents
        parallel_results = await self.executor.run_parallel_agents(tasks)
        
        # Quality reviewer needs results from both, so run it after
        if 'quality_reviewer' in agents:
            # Update context with parallel results
            for agent_name, result in parallel_results.items():
                if result['status'] == 'success':
                    context[f'{agent_name}_result'] = result['result']
            
            quality_result = await self.executor.run_agent_async(
                agents['quality_reviewer'].review,
                context['code'],
                context['language'],
                tools=context['tools'],
                analysis_context=context.get('code_analyzer_result'),
                security_context=context.get('security_checker_result')
            )
            
            parallel_results['quality_reviewer'] = quality_result
        
        return parallel_results
    
    async def _execute_hybrid(
        self,
        agents: Dict[str, Callable],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute with hybrid approach: parallel groups, sequential between groups"""
        
        # Group 1: Independent analyses (parallel)
        group1 = []
        if 'code_analyzer' in agents:
            group1.append({
                'name': 'code_analyzer',
                'func': agents['code_analyzer'].analyze,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        if 'security_checker' in agents:
            group1.append({
                'name': 'security_checker',
                'func': agents['security_checker'].check,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        # Group 2: Synthesis (depends on Group 1)
        group2 = []
        if 'quality_reviewer' in agents:
            group2.append({
                'name': 'quality_reviewer',
                'func': agents['quality_reviewer'].review,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        # Execute hybrid pipeline
        return await self.executor.run_hybrid_pipeline([group1, group2], context)
    
    async def _execute_sequential(
        self,
        agents: Dict[str, Callable],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents sequentially (current behavior)"""
        tasks = []
        
        if 'code_analyzer' in agents:
            tasks.append({
                'name': 'code_analyzer',
                'func': agents['code_analyzer'].analyze,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        if 'security_checker' in agents:
            tasks.append({
                'name': 'security_checker',
                'func': agents['security_checker'].check,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        if 'quality_reviewer' in agents:
            tasks.append({
                'name': 'quality_reviewer',
                'func': agents['quality_reviewer'].review,
                'args': (context['code'], context['language']),
                'kwargs': {'tools': context['tools']}
            })
        
        return await self.executor.run_sequential_with_context(tasks, context)
    
    def close(self):
        """Clean up resources"""
        self.executor.close()

# Utility function for easy usage
async def run_agents_parallel(
    agents: Dict[str, Callable],
    code: str,
    language: str,
    memory_bank: Any,
    tools: Any,
    mode: str = "hybrid"
) -> Dict[str, Any]:
    """
    Convenience function to run agents in parallel
    
    Args:
        agents: Dict of agent instances
        code: Code to review
        language: Programming language
        memory_bank: Shared memory
        tools: Analysis tools
        mode: 'sequential', 'parallel', or 'hybrid'
    """
    pipeline = AgentPipeline(execution_mode=mode)
    try:
        results = await pipeline.execute(agents, code, language, memory_bank, tools)
        return results
    finally:
        pipeline.close()
