import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

export async function GET() {
  try {
    // Read the evaluation results
    const resultsPath = join(process.cwd(), 'mind_eval_benchmark', 'results', 'summary.json');
    
    try {
      const fileContents = await readFile(resultsPath, 'utf-8');
      const results = JSON.parse(fileContents);
      
      return NextResponse.json(results);
    } catch (error: any) {
      // If file doesn't exist, return a message
      if (error.code === 'ENOENT') {
        return NextResponse.json(
          { 
            error: 'No evaluation results found',
            message: 'Please run the evaluation script first: python scripts/run_mind_eval.py'
          },
          { status: 404 }
        );
      }
      throw error;
    }
  } catch (error: any) {
    console.error('Error reading evaluation results:', error);
    return NextResponse.json(
      { error: 'Failed to read evaluation results', details: error.message },
      { status: 500 }
    );
  }
}
