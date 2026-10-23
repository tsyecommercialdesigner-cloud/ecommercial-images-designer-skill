/** Classify the actual native turn; an end event alone is not success. */
export function classifyTrial(end, answer) {
  if (end?.reason?.kind !== 'completed')
    return {status:'failed',error:JSON.stringify(end?.reason??{kind:'missing'})};
  if (!answer.trim()) return {status:'failed',error:'Completed turn has no final text answer'};
  return {status:'completed'};
}
