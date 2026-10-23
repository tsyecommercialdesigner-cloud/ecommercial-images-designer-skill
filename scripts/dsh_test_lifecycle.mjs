/** Host-side helpers: use the installed factory lifecycle, never delete history. */
export async function createOwnedTestAgent(ctx, sessionId, cwd, owner) {
  if (!/^session-76d8-[a-f0-9-]{36}$/.test(sessionId) || !owner || !cwd)
    throw Error('Explicit test identity, owner and cwd required');
  const key = Symbol.for('dsh76d8.owned-handles');
  const handles = ctx[key] ??= new Map();
  if (handles.has(sessionId) || ctx.agents.get(sessionId) || ctx.sessions.get(sessionId))
    throw Error('Refusing to adopt an existing session');
  const commands = ctx.sessionController.commands.agents;
  const composition = await commands.composeAgent();
  // Same factory/options/preset as SessionAgentCommands.createAgent(), but retain
  // its documented teardown capability instead of discarding the handle.
  const handle = await ctx.agents.create({sessionId, agentOptions:commands.agentOptions(),
    meta:{cwd,...composition.agentPreset===undefined?{}:{agentPreset:composition.agentPreset}},
    setup:composition.setup});
  handles.set(sessionId,{owner,cwd,handle});
  return {sessionId,agentPreset:composition.agentPreset,lifecycle:'owned-factory-handle'};
}

export async function releaseOwnedTestAgent(ctx, sessionId, cwd, owner) {
  const handles = ctx[Symbol.for('dsh76d8.owned-handles')];
  const entry = handles?.get(sessionId);
  if (!entry || entry.owner!==owner || entry.cwd!==cwd)
    throw Error('No matching owned lifecycle capability; nothing released');
  const agent = entry.handle.agent;
  if (ctx.agents.get(sessionId)!==agent || agent.session.header.cwd!==cwd)
    throw Error('Live identity mismatch; nothing released');
  // The documented disposer drains active work and closes persistence. Never
  // detach registry entries, dispose scopes directly, archive or delete files.
  const before = agent.session.snapshotEvents();
  await entry.handle.dispose();
  if (ctx.agents.get(sessionId) || ctx.sessions.get(sessionId))
    throw Error('Runtime still live after disposal');
  const cold = await ctx.sessionQuery.readSession(sessionId);
  if (cold.session.id!==sessionId || cold.session.cwd!==cwd ||
      JSON.stringify(cold.events.slice(0,before.length))!==JSON.stringify(before))
    throw Error('Persisted history does not retain the pre-disposal event prefix');
  if (ctx.agents.get(sessionId) || ctx.sessions.get(sessionId))
    throw Error('Cold verification unexpectedly reactivated runtime');
  handles.delete(sessionId);
  return {released:true,persisted:true,beforeEvents:before.length,
    persistedEvents:cold.events.length,runtimeAgentAbsent:true,runtimeSessionAbsent:true,
    events:cold.events};
}
