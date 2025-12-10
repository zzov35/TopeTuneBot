from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Numeric,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# SQLite-файл в корне проекта. Потом легко поменяем на PostgreSQL.
engine = create_engine("sqlite:///toptune.db", echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    models = relationship("CarModel", back_populates="brand")

    def __repr__(self):
        return f"<Brand {self.name}>"


class CarModel(Base):
    __tablename__ = "car_models"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    name = Column(String(50), nullable=False)

    brand = relationship("Brand", back_populates="models")
    fitments = relationship("ProductFitment", back_populates="car_model")

    def __repr__(self):
        return f"<CarModel {self.brand.name} {self.name}>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # bodykit, wheels, exhaust и т.д.
    description = Column(Text)
    price = Column(Numeric(12, 2))
    is_active = Column(Boolean, default=True)

    # новое поле: file_id фото из Telegram
    photo_file_id = Column(String(255))

    fitments = relationship("ProductFitment", back_populates="product")

    def __repr__(self):
        return f"<Product {self.name}>"


class ProductFitment(Base):
    __tablename__ = "product_fitments"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    car_model_id = Column(Integer, ForeignKey("car_models.id"), nullable=False)
    notes = Column(Text)

    product = relationship("Product", back_populates="fitments")
    car_model = relationship("CarModel", back_populates="fitments")

    def __repr__(self):
        return f"<Fitment {self.product.name} -> {self.car_model}>"


# --- служебные функции --- #

def init_db():
    """Создаём таблицы (если их ещё нет)."""
    Base.metadata.create_all(bind=engine)


def seed_demo_data():
    """
    Заполняем стартовые данные:
    Mercedes, BMW, модели и один демо-товар.
    Запускать можно много раз — данные не продублируются.
    """
    session = SessionLocal()
    try:
        # если бренды уже есть — считаем, что данные засеяны
        if session.query(Brand).count() > 0:
            return

        mercedes = Brand(name="Mercedes")
        bmw = Brand(name="BMW")
        session.add_all([mercedes, bmw])
        session.flush()  # чтобы у брендов появились id

        cla = CarModel(name="CLA", brand=mercedes)
        e_class = CarModel(name="E-Class", brand=mercedes)
        c_class = CarModel(name="C-Class", brand=mercedes)

        series_3 = CarModel(name="3 Series", brand=bmw)
        series_4 = CarModel(name="4 Series", brand=bmw)
        series_5 = CarModel(name="5 Series", brand=bmw)

        session.add_all([cla, e_class, c_class, series_3, series_4, series_5])

        # Демо-товар, чтобы было что показывать
        kit_cla = Product(
            name="AMG-style обвес для CLA",
            category="bodykit",
            description="Комплект обвеса AMG-style для Mercedes CLA. Бампер, пороги, диффузор.",
            price=150000,
            is_active=True,
        )
        session.add(kit_cla)
        session.flush()

        fitment_cla = ProductFitment(product=kit_cla, car_model=cla, notes="Подходит для CLA C118, 2019+")
        session.add(fitment_cla)

        session.commit()
    finally:
        session.close()


def get_products_for_model(brand_name: str, model_name: str):
    """
    Вернёт список продуктов для заданной марки и модели.
    Используем это внутри бота.
    """
    session = SessionLocal()
    try:
        q = (
            session.query(Product)
            .join(ProductFitment)
            .join(CarModel)
            .join(Brand)
            .filter(
                Brand.name == brand_name,
                CarModel.name == model_name,
                Product.is_active.is_(True),
            )
        )
        return q.all()
    finally:
        session.close()

def add_product_with_fitments(
    name: str,
    brand_name: str,
    model_names: list[str],
    photo_file_id: str | None = None,
    category: str = "bodykit",
    description: str | None = None,
    price: float | None = None,
    years: str | None = None,   # <--- НОВОЕ
) -> int:
    """
    Создаёт товар, при необходимости создаёт марку/модели
    и привязывает товар к этим моделям.
    Возвращает id товара.
    """
    session = SessionLocal()
    try:
        # бренд
        brand = session.query(Brand).filter_by(name=brand_name).first()
        if not brand:
            brand = Brand(name=brand_name)
            session.add(brand)
            session.flush()

        # модели
        models: list[CarModel] = []
        for model_name in model_names:
            model = (
                session.query(CarModel)
                .filter_by(brand_id=brand.id, name=model_name)
                .first()
            )
            if not model:
                model = CarModel(name=model_name, brand=brand)
                session.add(model)
                session.flush()
            models.append(model)

        # товар
        product = Product(
            name=name,
            category=category,
            description=description,
            price=price,
            is_active=True,
            photo_file_id=photo_file_id,
        )
        session.add(product)
        session.flush()

        # привязки (в notes кладём годы выпуска)
        for model in models:
            fit = ProductFitment(product=product, car_model=model, notes=years)
            session.add(fit)

        session.commit()
        return product.id
    finally:
        session.close()

def get_all_brands():
    """Список всех марок для меню."""
    session = SessionLocal()
    try:
        return session.query(Brand).order_by(Brand.name).all()
    finally:
        session.close()


def get_models_for_brand_id(brand_id: int):
    """Список моделей выбранной марки для меню."""
    session = SessionLocal()
    try:
        return (
            session.query(CarModel)
            .filter(CarModel.brand_id == brand_id)
            .order_by(CarModel.name)
            .all()
        )
    finally:
        session.close()


def create_brand(name: str) -> int:
    """Создать марку (если нет) и вернуть её id."""
    session = SessionLocal()
    try:
        existing = session.query(Brand).filter_by(name=name).first()
        if existing:
            return existing.id
        brand = Brand(name=name)
        session.add(brand)
        session.commit()
        return brand.id
    finally:
        session.close()


def create_model(brand_id: int, name: str) -> int:
    """Создать модель (если нет) и вернуть её id."""
    session = SessionLocal()
    try:
        existing = (
            session.query(CarModel)
            .filter_by(brand_id=brand_id, name=name)
            .first()
        )
        if existing:
            return existing.id
        model = CarModel(brand_id=brand_id, name=name)
        session.add(model)
        session.commit()
        return model.id
    finally:
        session.close()


def get_brand_and_model_names(brand_id: int, model_id: int):
    """Вернуть (название_марки, название_модели) по id."""
    session = SessionLocal()
    try:
        brand = session.get(Brand, brand_id)
        model = session.get(CarModel, model_id)
        return (
            brand.name if brand else None,
            model.name if model else None,
        )
    finally:
        session.close()

def delete_product_by_id(product_id: int) -> bool:
    """
    Удаляет товар и все его привязки по id.
    Возвращает True, если товар был найден и удалён, False — если не найден.
    """
    session = SessionLocal()
    try:
        product = session.get(Product, product_id)
        if not product:
            return False

        # сначала удаляем fitments
        session.query(ProductFitment).filter_by(product_id=product_id).delete()

        # затем сам товар
        session.delete(product)
        session.commit()
        return True
    finally:
        session.close()


if __name__ == "__main__":
    # Если запустить db.py напрямую — создаст БД и засеет демо-данные
    init_db()
    seed_demo_data()
    print("База и демо-данные готовы (toptune.db).")
