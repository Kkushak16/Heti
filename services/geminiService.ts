import { GoogleGenerativeAI } from "@google/generative-ai";

const apiKey = process.env.API_KEY || "";
const ai = new GoogleGenerativeAI( apiKey );

export const checkApiKey = (): boolean => {
  return !!apiKey;
};

// Helper to clean Markdown code blocks
const extractCode = (text: string): string => {
  const match = text.match(/```(?:\w+)?\n([\s\S]*?)```/);
  return match ? match[1].trim() : text;
};

// Helper to append sources from grounding metadata
const appendSources = (text: string, response: any): string => {
  const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
  if (!chunks || chunks.length === 0) return text;

  let sourcesMd = "\n\n### 🌐 Verified Sources\n";
  chunks.forEach((chunk: any, index: number) => {
    if (chunk.web?.uri && chunk.web?.title) {
      sourcesMd += `- [${chunk.web.title}](${chunk.web.uri})\n`;
    }
  });
  return text + sourcesMd;
};

export const modernizeCode = async (content: string, sourceLang: string, isUrl: boolean = false): Promise<{ code: string; explanation: string }> => {
  if (!apiKey) throw new Error("API Key missing");

  let prompt = "";
  let tools: any = [];

  if (isUrl) {
    prompt = `
      You are an expert Senior Full Stack Engineer.
      Analyze the website at this URL: ${content}
      
      Based on the visible structure and typical patterns for this type of site:
      1. Create a MODERN boilerplate implementation using React (TypeScript) and Tailwind CSS that replicates the core functionality and design of this site but with a modern stack.
      2. In the explanation, describe the likely legacy stack it might be replacing and why the new stack is better.
      
      Provide the response in two parts:
      1. The code block.
      2. The explanation.
    `;
    // Use search to "see" the website
    tools = [{ googleSearch: {} }];
  } else {
    const langInstruction = sourceLang === 'Auto Detect' 
      ? "Analyze the code to automatically detect the source language." 
      : `The source language is ${sourceLang}.`;

    prompt = `
      You are an expert Senior Full Stack Engineer. 
      ${langInstruction}
      
      Convert the following legacy code into modern, clean, and secure React (TypeScript) and/or HTML5/CSS3.
      
      Legacy Code:
      ${content}

      Provide the response in two parts:
      1. The converted modern code in a single code block.
      2. A brief explanation of the changes.
    `;
  }

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
    config: {
      temperature: 0.2,
      tools: tools
    }
  });

  const fullText = response.text || '';
  const codeBlock = extractCode(fullText);
  let explanation = fullText.replace(/```[\s\S]*?```/g, '').trim();
  
  // Append sources if search was used
  if (isUrl) {
    explanation = appendSources(explanation, response);
  }

  return {
    code: codeBlock,
    explanation: explanation || "Conversion complete. See code above."
  };
};

export const auditWebsite = async (content: string, isUrl: boolean = false): Promise<{ markdown: string; score: number }> => {
  if (!apiKey) throw new Error("API Key missing");

  let prompt = "";
  let tools: any = [];

  if (isUrl) {
    prompt = `
      Perform a comprehensive security and performance audit of the website at: ${content}
      
      Look for:
      1. Common vulnerabilities (exposed headers, lack of HTTPS, mixed content).
      2. UX/UI glitches visible to a user.
      3. Performance bottlenecks inferred from the site type.
      
      Return a JSON object with:
      - "score": A number between 0 and 100.
      - "report": A detailed Markdown report.
    `;
    tools = [{ googleSearch: {} }];
  } else {
    prompt = `
      Analyze the following code snippet or system description for security flaws, glitches, and performance bottlenecks.
      
      Content:
      ${content}

      Return a JSON object with:
      - "score": A number between 0 and 100.
      - "report": A detailed Markdown report.
    `;
  }
  
  const config: any = {
    responseMimeType: "application/json",
  };
  
  if (isUrl) {
     config.tools = [{ googleSearch: {} }];
  } else {
     config.responseSchema = {
        type: Type.OBJECT,
        properties: {
          score: { type: Type.NUMBER },
          report: { type: Type.STRING }
        },
        required: ["score", "report"]
      };
  }

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
    config: config
  });

  let result;
  try {
    result = JSON.parse(response.text || '{}');
  } catch (e) {
    result = { score: 0, report: response.text || "Error parsing report." };
  }

  let reportMarkdown = result.report || "No report generated.";
  if (isUrl) {
    reportMarkdown = appendSources(reportMarkdown, response);
  }

  return {
    markdown: reportMarkdown,
    score: result.score || 0
  };
};

export const suggestUIUX = async (instruction: string, url: string = '', generateCode: boolean = false): Promise<string> => {
  if (!apiKey) throw new Error("API Key missing");

  let prompt = "";
  let tools: any = [];

  // When generating code, we act as a frontend architect.
  const role = generateCode 
    ? "You are an expert Frontend Architect and UI Engineer." 
    : "You are a world-class UI/UX Designer.";
    
  const outputInstruction = generateCode 
    ? "Based on the analysis and vision, generate a complete, production-ready React component (using Tailwind CSS) that implements a significant visual upgrade. Return ONLY the code inside a markdown code block." 
    : "Provide high-impact UI/UX recommendations, critiquing the current site against the user's vision and modern trends (Anti-Gravity, Glassmorphism, Brutalism). Focus on Visual Hierarchy, Accessibility, and User Flow. Format as Markdown.";

  if (url) {
    tools = [{ googleSearch: {} }];
    prompt = `
      ${role}
      Analyze the website at: ${url}
      
      The user wants to improve it with this specific vision or problem: "${instruction}".
      
      ${outputInstruction}
    `;
  } else {
    prompt = `
      ${role}
      The user wants to design a website with this description: "${instruction}".
      
      ${outputInstruction}
    `;
  }

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
    config: { tools }
  });

  let text = response.text || "No output available.";
  if (url && !generateCode) {
    // Only append sources if we are not just dumping code, otherwise it breaks the code block cleanliness usually
    text = appendSources(text, response);
  }
  return text;
};

export const suggestGrowth = async (content: string, isUrl: boolean = false): Promise<string> => {
  if (!apiKey) throw new Error("API Key missing");

  let prompt = "";
  let tools: any = [];

  if (isUrl) {
    prompt = `
      You are a Growth Hacker and SEO Expert.
      Analyze the website at: ${content}
      
      Suggest strategies to increase reach, improve SEO, and drive engagement.
      Include keyword strategy, content marketing ideas, and technical SEO fixes.
      
      Format as Markdown.
    `;
    tools = [{ googleSearch: {} }];
  } else {
    prompt = `
      You are a Growth Hacker and SEO Expert.
      Analyze the following content or business description:
      ${content}
      
      Suggest strategies to increase reach, improve SEO, and drive engagement.
      Format as Markdown.
    `;
  }

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash', 
    contents: prompt,
    config: { tools }
  });

  let text = response.text || "No growth strategy available.";
  if (isUrl) {
    text = appendSources(text, response);
  }
  return text;
};