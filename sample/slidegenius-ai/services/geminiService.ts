/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import { GoogleGenAI, Modality } from "@google/genai";
import { ComplexityLevel, VisualStyle, SearchResultItem, Language, SlideOutline, UploadedFile } from "../types";

// Create a fresh client for every request
const getAi = () => {
  return new GoogleGenAI({ apiKey: process.env.API_KEY });
};

// gemini-3-pro-preview for logic/text
const TEXT_MODEL = 'gemini-3-pro-preview';
// gemini-3-pro-image-preview (Nano Banana Pro) for visuals
const IMAGE_MODEL = 'gemini-3-pro-image-preview';

const getStyleInstruction = (style: VisualStyle): string => {
  switch (style) {
    case '现代简约': return "Style: Minimalist, plenty of white space, sans-serif typography, soft pastel accents. Professional and airy.";
    case '商务科技': return "Style: Fortune 500 business style. Navy blues, greys, structured layouts, official look, subtle grid lines.";
    case '创意艺术': return "Style: Bold colors, artistic shapes, dynamic composition. High energy.";
    case '深色模式': return "Style: Dark background (slate/black), bright neon or white text, sleek and modern.";
    case '自然清新': return "Style: Organic shapes, green and earth tones, soft lighting.";
    default: return "Style: High-quality professional presentation.";
  }
};

export const generatePresentationOutline = async (
  input: string,
  attachedFile: UploadedFile | null,
  level: ComplexityLevel,
  style: VisualStyle,
  language: Language,
  slideCount: number = 5
): Promise<{ outline: SlideOutline[], sources: SearchResultItem[] }> => {
  
  // If file is attached (PDF), we treat it as an Article source
  const isArticle = input.length > 250 || attachedFile !== null;
  const styleInstr = getStyleInstruction(style);
  
  // Base prompt instruction
  const baseInstruction = `
    You are an expert presentation designer.
    Role: Create a structured outline for a ${slideCount}-slide presentation.
    
    Audience Level: ${level}
    Language: ${language} (CRITICAL: The JSON content, title, and body MUST be in ${language})
    
    Output Rules:
    1. Create exactly ${slideCount} slides.
    2. Slide 1 must be a Title Slide.
    3. The final slide must be a Conclusion/Summary.
    4. Return the output strictly as a JSON array of objects.
    
    JSON Format:
    [
      {
        "title": "Slide Title (In ${language})",
        "content": "Key bullet points for the slide text (max 30 words, In ${language})",
        "visualDescription": "Detailed prompt for an AI image generator to create this slide background and layout. Include placement of text placeholders. ${styleInstr}"
      }
    ]
  `;

  let promptText = "";

  if (isArticle) {
    promptText = `
      ${baseInstruction}
      
      Analyze the provided content (text and/or attached document) to create the deck.
    `;
    
    if (input) {
      promptText += `\n\nCONTENT TO ANALYZE:\n"${input.substring(0, 20000)}"`;
    }

  } else {
    // Topic Mode (Research)
    promptText = `
      ${baseInstruction}
      
      Task: Research the topic: "${input}" and create the deck.
      **Use Google Search to find accurate facts.**
    `;
  }

  const config = isArticle ? {} : { tools: [{ googleSearch: {} }] };
  
  // Construct parts
  const parts: any[] = [{ text: promptText }];
  
  if (attachedFile && attachedFile.type === 'application/pdf') {
     parts.push({
       inlineData: {
         mimeType: 'application/pdf',
         data: attachedFile.data // Expecting base64 without prefix
       }
     });
  }

  const response = await getAi().models.generateContent({
    model: TEXT_MODEL,
    contents: { parts },
    config: config,
  });

  const text = response.text || "";
  
  // Extract Sources if available
  const sources: SearchResultItem[] = [];
  const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
  if (chunks) {
    chunks.forEach(chunk => {
      if (chunk.web?.uri && chunk.web?.title) {
        sources.push({
          title: chunk.web.title,
          url: chunk.web.uri
        });
      }
    });
  }
  // Dedup sources
  const uniqueSources = Array.from(new Map(sources.map(item => [item.url, item])).values());

  // Parse JSON
  let outline: SlideOutline[] = [];
  try {
    const jsonMatch = text.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      outline = JSON.parse(jsonMatch[0]);
    } else {
      throw new Error("Could not parse JSON outline");
    }
  } catch (e) {
    console.error("JSON Parse Error", e);
    // Fallback manual parse if JSON fails (simple resilience)
    outline = [
      { title: "生成失败", content: "无法解析大纲结构，请重试。", visualDescription: "Generic professional background" }
    ];
  }

  return { outline, sources: uniqueSources };
};

export const generateSlideImage = async (slide: SlideOutline): Promise<string> => {
  // Enhancing the prompt to ensure better text rendering in the image
  const prompt = `
    Create a high-quality 16:9 presentation slide image.
    
    TEXT ON SLIDE (Render this text clearly):
    HEADLINE: ${slide.title}
    BODY COPY: ${slide.content}
    
    DESIGN INSTRUCTIONS:
    ${slide.visualDescription}
    
    CRITICAL:
    - The image MUST contain the text provided above.
    - The text must be legible, large, and professional.
    - Use a 16:9 aspect ratio layout.
    - Do not include messy or gibberish text.
  `;

  const response = await getAi().models.generateContent({
    model: IMAGE_MODEL,
    contents: {
      parts: [{ text: prompt }]
    },
    config: {
      responseModalities: [Modality.IMAGE],
    }
  });

  const part = response.candidates?.[0]?.content?.parts?.[0];
  if (part && part.inlineData && part.inlineData.data) {
    return `data:image/png;base64,${part.inlineData.data}`;
  }
  throw new Error("Failed to generate slide image");
};