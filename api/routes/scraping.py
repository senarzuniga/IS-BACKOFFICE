from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from backoffice.scraping.high_quality_scraper import scraper
import json
import uuid
import os
from glob import glob

router = APIRouter(prefix="/api/scraping", tags=["scraping"])

class ScrapeRequest(BaseModel):
    url: str
    min_width: int = 800
    recursive: bool = False
    max_pages: int = 5
    max_images: int = 50
    webhook_url: Optional[str] = None

class ScrapeResponse(BaseModel):
    task_id: str
    status: str
    message: str

# Almacenamiento temporal de tareas
scraping_tasks = {}

@router.post("/scrape", response_model=ScrapeResponse)
async def start_scraping(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Inicia un trabajo de scraping en segundo plano
    """
    task_id = str(uuid.uuid4())
    
    scraping_tasks[task_id] = {
        "status": "pending",
        "url": request.url,
        "created_at": None,
        "progress": 0
    }
    
    background_tasks.add_task(
        run_scraping_task,
        task_id,
        request
    )
    
    return ScrapeResponse(
        task_id=task_id,
        status="started",
        message="Scraping job started in background"
    )

async def run_scraping_task(task_id: str, request: ScrapeRequest):
    """Ejecuta la tarea de scraping en segundo plano"""
    try:
        scraping_tasks[task_id]["status"] = "running"
        scraping_tasks[task_id]["progress"] = 0
        
        # Ejecutar scraping
        results = scraper.scrape_website(
            url=request.url,
            min_width=request.min_width,
            recursive=request.recursive,
            max_pages=request.max_pages
        )
        
        scraping_tasks[task_id]["progress"] = 50
        
        # Descargar imágenes
        if results['images']:
            downloaded = scraper.download_images(
                results['images'],
                max_images=request.max_images
            )
            results['downloaded_images'] = downloaded
        else:
            results['downloaded_images'] = []
        
        scraping_tasks[task_id]["status"] = "completed"
        scraping_tasks[task_id]["results"] = results
        scraping_tasks[task_id]["progress"] = 100
        
    except Exception as e:
        scraping_tasks[task_id]["status"] = "failed"
        scraping_tasks[task_id]["error"] = str(e)

@router.get("/status/{task_id}")
async def get_scraping_status(task_id: str):
    """Obtiene el estado de una tarea de scraping"""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = scraping_tasks[task_id].copy()
    # No incluir results en la respuesta de estado
    if 'results' in task:
        del task['results']
    
    return task

@router.get("/results/{task_id}")
async def get_scraping_results(task_id: str):
    """Obtiene los resultados completados de una tarea de scraping"""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = scraping_tasks[task_id]
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Task status is {task['status']}, not completed")
    
    if 'results' not in task:
        raise HTTPException(status_code=400, detail="Results not available")
    
    return task['results']

@router.get("/images")
async def list_scraped_images(limit: int = 20, offset: int = 0):
    """Lista las imágenes descargadas"""
    
    image_files = glob("scraped_images/*.jpg") + glob("scraped_images/*.png")
    image_files = sorted(image_files, reverse=True)
    
    total = len(image_files)
    image_files = image_files[offset:offset+limit]
    
    images = []
    for img_path in image_files:
        try:
            images.append({
                "filename": os.path.basename(img_path),
                "path": img_path,
                "size_bytes": os.path.getsize(img_path)
            })
        except:
            pass
    
    return {
        "images": images,
        "total": total,
        "offset": offset,
        "limit": limit
    }

@router.get("/images/{filename}")
async def get_image_file(filename: str):
    """Obtiene una imagen descargada"""
    from fastapi.responses import FileResponse
    
    # Validar nombre de archivo para seguridad
    if '/' in filename or '\\' in filename or filename.startswith('.'):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = os.path.join("scraped_images", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(filepath)

@router.get("/health")
async def scraping_health():
    """Verifica el estado del servicio de scraping"""
    return {
        "status": "healthy",
        "active_tasks": len([t for t in scraping_tasks.values() if t['status'] == 'running']),
        "completed_tasks": len([t for t in scraping_tasks.values() if t['status'] == 'completed']),
        "total_images": len(glob("scraped_images/*.jpg") + glob("scraped_images/*.png"))
    }

@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Elimina una tarea del registro"""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del scraping_tasks[task_id]
    
    return {
        "status": "deleted",
        "task_id": task_id
    }
