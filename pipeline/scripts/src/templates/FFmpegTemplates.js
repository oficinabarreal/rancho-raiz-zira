export const FFmpegTemplates = {
  ranchoRaizClassic: {
    name: 'Rancho Raiz - Classic',
    duration: 10,
    fps: 30,
    resolution: '1080x1920',
    colorGrading: 'eq=saturation=1.15:contrast=1.05:brightness=0.02',
    texts: [
      {
        text: 'RANCHO RAÍZ',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 100,
        x: '(w-tw)/2',
        y: '(h-th)/2-70',
        startTime: 1.5,
        endTime: 3.5,
        fadeIn: 1.5,
        fadeOut: 1.0
      },
      {
        text: 'CONEXIÓN ANDINA',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 38,
        x: '(w-tw)/2',
        y: '(h-th)/2+60',
        startTime: 0.8,
        endTime: 3.5,
        fadeIn: 1.2,
        fadeOut: 1.0
      },
      {
        text: 'TU REFUGIO',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 100,
        x: '(w-tw)/2',
        y: '(h-th)/2-70',
        startTime: 3.5,
        endTime: 7.0,
        fadeIn: 1.0,
        fadeOut: 1.0
      },
      {
        text: 'ENTRE MONTAÑAS',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 38,
        x: '(w-tw)/2',
        y: '(h-th)/2+60',
        startTime: 4.0,
        endTime: 7.0,
        fadeIn: 1.0,
        fadeOut: 1.0
      },
      {
        text: 'RESERVA HOY',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 90,
        x: '(w-tw)/2',
        y: '(h-th)/2-70',
        startTime: 7.0,
        endTime: 10.0,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: '@RANCHORAIZ.POSADA',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 38,
        x: '(w-tw)/2',
        y: '(h-th)/2+60',
        startTime: 7.5,
        endTime: 10.0,
        fadeIn: 1.0,
        fadeOut: 0
      }
    ]
  },
  
  climaDiario: {
    name: 'Clima Diario',
    duration: 8,
    fps: 30,
    resolution: '1080x1920',
    colorGrading: 'eq=saturation=1.1:contrast=1.05',
    texts: [
      {
        text: 'EL CLIMA EN RANCHO RAÍZ',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 70,
        x: '(w-tw)/2',
        y: '150',
        startTime: 0,
        endTime: 8,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: '{{temperatura}}',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 180,
        x: '(w-tw)/2',
        y: '(h-th)/2-100',
        startTime: 1.5,
        endTime: 8,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: '{{estado}}',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 50,
        x: '(w-tw)/2',
        y: '(h-th)/2+80',
        startTime: 2.0,
        endTime: 8,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: '{{consejo}}',
        font: 'Roboto-Light.ttf',
        color: '0xEAE4D3',
        size: 40,
        x: '(w-tw)/2',
        y: '(h-th)/2+180',
        startTime: 2.5,
        endTime: 8,
        fadeIn: 1.0,
        fadeOut: 0
      }
    ]
  },
  
  minimal: {
    name: 'Minimal - Solo Logo',
    duration: 5,
    fps: 30,
    resolution: '1080x1920',
    colorGrading: 'eq=saturation=1.05:contrast=1.02',
    texts: [
      {
        text: '@RANCHORAIZ.POSADA',
        font: 'Roboto-Medium.ttf',
        color: '0xffffff',
        size: 42,
        x: '(w-tw)/2',
        y: 'h-th-120',
        startTime: 1.0,
        endTime: 5.0,
        fadeIn: 0.8,
        fadeOut: 0
      }
    ]
  }
};

export function generateDrawText(textObj) {
  const { text, font, color, size, x, y, startTime, endTime, fadeIn, fadeOut } = textObj;
  
  let alphaExpr = '1';
  
  if (fadeIn > 0 || fadeOut > 0) {
    const parts = [];
    
    if (fadeIn > 0) {
      parts.push(`if(lt(t,${startTime}),0,if(lt(t,${startTime + fadeIn}),(t-${startTime})/${fadeIn}`);
    } else {
      parts.push(`if(lt(t,${startTime}),0`);
    }
    
    if (fadeOut > 0) {
      const fadeStart = endTime - fadeOut;
      parts.push(`,if(gt(t,${fadeStart}),1-(t-${fadeStart})/${fadeOut},1)`);
    } else {
      parts.push(`,if(gt(t,${endTime}),0,1)`);
    }
    
    parts.push(')'.repeat(parts.length - 1));
    alphaExpr = parts.join('');
  }
  
  return `drawtext=fontfile=/system/fonts/${font}:text='${text}':fontcolor=${color}:fontsize=${size}:x='${x}':y='${y}':alpha='${alphaExpr}'`;
}

export function buildFFmpegCommand(inputVideo, template, outputPath, variables = {}) {
  const texts = template.texts.map(t => {
    let text = t.text;
    Object.entries(variables).forEach(([key, value]) => {
      text = text.replace(`{{${key}}}`, value);
    });
    return { ...t, text };
  });
  
  const drawTextFilters = texts.map(generateDrawText).join(',');
  
  const filterComplex = `[0:v]fps=${template.fps},scale=${template.resolution}:force_original_aspect_ratio=increase,crop=${template.resolution},${template.colorGrading},${drawTextFilters}[video]`;
  
  return `ffmpeg -i "${inputVideo}" -filter_complex "${filterComplex}" -map "[video]" -map 0:a? -t ${template.duration} -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k "${outputPath}" -y`;
}
