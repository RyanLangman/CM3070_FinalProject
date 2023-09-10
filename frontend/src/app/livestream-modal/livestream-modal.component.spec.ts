import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LivestreamModalComponent } from './livestream-modal.component';

describe('LivestreamModalComponent', () => {
  let component: LivestreamModalComponent;
  let fixture: ComponentFixture<LivestreamModalComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [LivestreamModalComponent]
    });
    fixture = TestBed.createComponent(LivestreamModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
