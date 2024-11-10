package main

import (
	"database/sql"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	_ "modernc.org/sqlite"
)

type Livro struct {
	ID        int    `json:"id"`
	Titulo    string `json:"titulo"`
	Autor     string `json:"autor"`
	Genero    string `json:"genero"`
	Categoria string `json:"categoria"`
}

var db *sql.DB

func inicializarBD() error {
	var err error
	db, err = sql.Open("sqlite", "./biblioteca.db")
	if err != nil {
		return err
	}

	// Criar tabela de livros
	_, err = db.Exec(`
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            genero TEXT,
            categoria TEXT
        )
    `)
	return err
}

func main() {
	// Inicializar banco de dados
	if err := inicializarBD(); err != nil {
		log.Fatal("Erro ao inicializar banco de dados:", err)
	}
	defer db.Close()

	// Configurar Gin
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// Configurar CORS
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Origin, Content-Type")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Rotas
	r.GET("/livros", buscarLivros)
	r.GET("/livros/:id", buscarLivro)
	r.POST("/livros", criarLivro)
	r.PUT("/livros/:id", atualizarLivro)
	r.DELETE("/livros/:id", deletarLivro)

	// Iniciar servidor
	log.Println("Servidor iniciado em http://localhost:8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}

func buscarLivros(c *gin.Context) {
	rows, err := db.Query("SELECT id, titulo, autor, genero, categoria FROM livros")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"erro": err.Error()})
		return
	}
	defer rows.Close()

	var livros []Livro
	for rows.Next() {
		var l Livro
		if err := rows.Scan(&l.ID, &l.Titulo, &l.Autor, &l.Genero, &l.Categoria); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"erro": err.Error()})
			return
		}
		livros = append(livros, l)
	}

	c.JSON(http.StatusOK, livros)
}

func buscarLivro(c *gin.Context) {
	var livro Livro
	err := db.QueryRow(
		"SELECT id, titulo, autor, genero, categoria FROM livros WHERE id = ?",
		c.Param("id"),
	).Scan(&livro.ID, &livro.Titulo, &livro.Autor, &livro.Genero, &livro.Categoria)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"erro": "Livro não encontrado"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"erro": err.Error()})
		return
	}

	c.JSON(http.StatusOK, livro)
}

func criarLivro(c *gin.Context) {
	var livro Livro
	if err := c.BindJSON(&livro); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"erro": err.Error()})
		return
	}

	result, err := db.Exec(
		"INSERT INTO livros (titulo, autor, genero, categoria) VALUES (?, ?, ?, ?)",
		livro.Titulo, livro.Autor, livro.Genero, livro.Categoria,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"erro": err.Error()})
		return
	}

	id, _ := result.LastInsertId()
	livro.ID = int(id)
	c.JSON(http.StatusCreated, livro)
}

func atualizarLivro(c *gin.Context) {
	var livro Livro
	if err := c.BindJSON(&livro); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"erro": err.Error()})
		return
	}

	_, err := db.Exec(
		"UPDATE livros SET titulo = ?, autor = ?, genero = ?, categoria = ? WHERE id = ?",
		livro.Titulo, livro.Autor, livro.Genero, livro.Categoria, c.Param("id"),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"erro": err.Error()})
		return
	}

	c.JSON(http.StatusOK, livro)
}

func deletarLivro(c *gin.Context) {
	_, err := db.Exec("DELETE FROM livros WHERE id = ?", c.Param("id"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"erro": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}
